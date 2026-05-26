use adobepy_protocol::{
    session_key, BridgeInbound, BridgeOutbound, BridgeSessionInfo, HostKind, RequestId,
    RpcErrorResponse, RpcRequest, RpcResponse, DEFAULT_TARGET, ERROR_BRIDGE_NOT_INSTALLED,
    ERROR_CAPABILITY, ERROR_INVALID_REQUEST, ERROR_PARSE, ERROR_SERIALIZATION, ERROR_TIMEOUT,
    ERROR_UNAUTHORIZED, JSONRPC_VERSION,
};
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Path, State};
use axum::http::{HeaderMap, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use futures_util::{SinkExt, StreamExt};
use serde::Serialize;
use serde_json::json;
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::net::TcpListener;
use tokio::sync::{mpsc, oneshot, Mutex, RwLock};

type DispatchResult = Result<RpcResponse, RpcErrorResponse>;
type ValidationResult = Result<(), Box<RpcErrorResponse>>;

struct PendingRequest {
    original_id: RequestId,
    session_key: String,
    connection_id: u64,
    sender: oneshot::Sender<DispatchResult>,
}

#[derive(Clone)]
struct BridgeSender {
    connection_id: u64,
    sender: mpsc::UnboundedSender<BridgeOutbound>,
}

#[derive(Debug, Clone)]
pub struct BrokerConfig {
    pub bind: SocketAddr,
    pub token: String,
    pub default_timeout_ms: u64,
}

impl Default for BrokerConfig {
    fn default() -> Self {
        Self {
            bind: SocketAddr::from(([127, 0, 0, 1], 47_391)),
            token: "dev-token".to_owned(),
            default_timeout_ms: 30_000,
        }
    }
}

#[derive(Clone)]
struct BrokerState {
    token: String,
    default_timeout_ms: u64,
    sessions: Arc<RwLock<HashMap<String, BridgeSessionInfo>>>,
    bridge_senders: Arc<RwLock<HashMap<String, BridgeSender>>>,
    pending: Arc<Mutex<HashMap<RequestId, PendingRequest>>>,
    next_dispatch_id: Arc<AtomicU64>,
    next_connection_id: Arc<AtomicU64>,
}

impl BrokerState {
    fn new(config: &BrokerConfig) -> Self {
        Self {
            token: config.token.clone(),
            default_timeout_ms: config.default_timeout_ms,
            sessions: Arc::new(RwLock::new(HashMap::new())),
            bridge_senders: Arc::new(RwLock::new(HashMap::new())),
            pending: Arc::new(Mutex::new(HashMap::new())),
            next_dispatch_id: Arc::new(AtomicU64::new(1)),
            next_connection_id: Arc::new(AtomicU64::new(1)),
        }
    }

    fn authorized(&self, headers: &HeaderMap) -> bool {
        self.token.is_empty()
            || headers
                .get("x-adobepy-token")
                .and_then(|value| value.to_str().ok())
                .is_some_and(|value| value == self.token)
    }

    async fn dispatch_request(&self, request: RpcRequest) -> DispatchResult {
        validate_request(&request).map_err(|error| *error)?;
        let target = request.target_or_default().to_owned();
        let key = session_key(request.host, &target);
        let (sender, session) = {
            let senders = self.bridge_senders.read().await;
            let sessions = self.sessions.read().await;
            (senders.get(&key).cloned(), sessions.get(&key).cloned())
        };
        let Some(sender) = sender else {
            return Err(RpcErrorResponse::new(
                Some(request.id.clone()),
                ERROR_BRIDGE_NOT_INSTALLED,
                format!(
                    "no bridge session is connected for host '{}' target '{}'",
                    request.host, target
                ),
            ));
        };
        let Some(session) = session else {
            return Err(RpcErrorResponse::new(
                Some(request.id.clone()),
                ERROR_BRIDGE_NOT_INSTALLED,
                "bridge session metadata is unavailable",
            ));
        };
        validate_capability_contract(&request, &target, &session).map_err(|error| *error)?;
        let timeout_ms = request
            .options
            .timeout_ms
            .unwrap_or(self.default_timeout_ms);
        let original_id = request.id.clone();
        let dispatch_id = RequestId::from_string(format!(
            "broker_{}",
            self.next_dispatch_id.fetch_add(1, Ordering::Relaxed)
        ));
        let mut bridge_request = request;
        bridge_request.id = dispatch_id.clone();
        let (tx, rx) = oneshot::channel();
        self.pending.lock().await.insert(
            dispatch_id.clone(),
            PendingRequest {
                original_id: original_id.clone(),
                session_key: key.clone(),
                connection_id: sender.connection_id,
                sender: tx,
            },
        );
        if sender
            .sender
            .send(BridgeOutbound::Request {
                request: bridge_request,
            })
            .is_err()
        {
            self.pending.lock().await.remove(&dispatch_id);
            return Err(RpcErrorResponse::new(
                Some(original_id),
                ERROR_BRIDGE_NOT_INSTALLED,
                "bridge disconnected before request could be sent",
            ));
        }
        match tokio::time::timeout(Duration::from_millis(timeout_ms), rx).await {
            Ok(Ok(result)) => result,
            Ok(Err(_)) => Err(RpcErrorResponse::new(
                Some(original_id),
                ERROR_BRIDGE_NOT_INSTALLED,
                "bridge response channel closed",
            )),
            Err(_) => {
                self.pending.lock().await.remove(&dispatch_id);
                Err(RpcErrorResponse::new(
                    Some(original_id),
                    ERROR_TIMEOUT,
                    format!("request timed out after {timeout_ms}ms"),
                ))
            }
        }
    }

    fn next_connection_id(&self) -> u64 {
        self.next_connection_id.fetch_add(1, Ordering::Relaxed)
    }

    async fn disconnect_session(&self, key: &str, connection_id: u64, message: impl Into<String>) {
        let message = message.into();
        let removed_current = {
            let mut senders = self.bridge_senders.write().await;
            if senders
                .get(key)
                .is_some_and(|current| current.connection_id == connection_id)
            {
                senders.remove(key);
                true
            } else {
                false
            }
        };
        if removed_current {
            self.sessions.write().await.remove(key);
        }
        let drained = {
            let mut pending = self.pending.lock().await;
            let ids: Vec<_> = pending
                .iter()
                .filter(|(_, request)| {
                    request.session_key == key && request.connection_id == connection_id
                })
                .map(|(id, _)| id.clone())
                .collect();
            ids.into_iter()
                .filter_map(|id| pending.remove(&id))
                .collect::<Vec<_>>()
        };
        for request in drained {
            let _ = request.sender.send(Err(RpcErrorResponse::new(
                Some(request.original_id),
                ERROR_BRIDGE_NOT_INSTALLED,
                message.clone(),
            )));
        }
    }
}

pub async fn run_broker(config: BrokerConfig) -> anyhow::Result<()> {
    let app = broker_router(BrokerState::new(&config));
    let listener = TcpListener::bind(config.bind).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

fn broker_router(state: BrokerState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/v1/capabilities", get(list_capabilities))
        .route("/v1/rpc", post(http_rpc))
        .route("/v1/client/ws", get(client_ws))
        .route("/v1/bridge/{host}/ws", get(bridge_ws))
        .with_state(state)
}

async fn health(State(state): State<BrokerState>) -> impl IntoResponse {
    Json(
        json!({"status": "ok", "sessions": state.sessions.read().await.len(), "protocol": "jsonrpc-2.0"}),
    )
}

async fn list_capabilities(State(state): State<BrokerState>, headers: HeaderMap) -> Response {
    if !state.authorized(&headers) {
        return unauthorized_response();
    }
    Json(
        state
            .sessions
            .read()
            .await
            .values()
            .cloned()
            .collect::<Vec<_>>(),
    )
    .into_response()
}

async fn http_rpc(
    State(state): State<BrokerState>,
    headers: HeaderMap,
    Json(request): Json<RpcRequest>,
) -> Response {
    if !state.authorized(&headers) {
        return Json(RpcErrorResponse::new(
            Some(request.id),
            ERROR_UNAUTHORIZED,
            "invalid or missing x-adobepy-token header",
        ))
        .into_response();
    }
    match state.dispatch_request(request).await {
        Ok(response) => Json(response).into_response(),
        Err(error) => Json(error).into_response(),
    }
}

async fn client_ws(
    State(state): State<BrokerState>,
    headers: HeaderMap,
    ws: WebSocketUpgrade,
) -> Response {
    if !state.authorized(&headers) {
        return unauthorized_response();
    }
    ws.on_upgrade(move |socket| client_socket(socket, state))
}

async fn bridge_ws(
    State(state): State<BrokerState>,
    Path(host): Path<String>,
    ws: WebSocketUpgrade,
) -> Response {
    let Ok(host) = host.parse::<HostKind>() else {
        return (StatusCode::BAD_REQUEST, "unknown host").into_response();
    };
    ws.on_upgrade(move |socket| bridge_socket(socket, state, host))
}

async fn client_socket(mut socket: WebSocket, state: BrokerState) {
    while let Some(Ok(message)) = socket.next().await {
        let response = match message {
            Message::Text(text) => match serde_json::from_str::<RpcRequest>(&text) {
                Ok(request) => match state.dispatch_request(request).await {
                    Ok(response) => serde_json::to_string(&response),
                    Err(error) => serde_json::to_string(&error),
                },
                Err(error) => serde_json::to_string(&RpcErrorResponse::new(
                    None,
                    ERROR_PARSE,
                    format!("invalid JSON-RPC request: {error}"),
                )),
            },
            Message::Close(_) => break,
            _ => continue,
        };
        let response = response.unwrap_or_else(|_| serialization_error_text(None));
        if socket.send(Message::Text(response.into())).await.is_err() {
            break;
        }
    }
}

async fn bridge_socket(mut socket: WebSocket, state: BrokerState, expected_host: HostKind) {
    let Some(Ok(Message::Text(first))) = socket.next().await else {
        return;
    };
    let Ok(BridgeInbound::Hello {
        token,
        target,
        capabilities,
    }) = serde_json::from_str::<BridgeInbound>(&first)
    else {
        return;
    };
    if !state.token.is_empty() && token != state.token {
        let _ = socket
            .send(Message::Text(
                serialize_wire(&RpcErrorResponse::new(
                    None,
                    ERROR_UNAUTHORIZED,
                    "invalid bridge token",
                ))
                .into(),
            ))
            .await;
        return;
    }
    if capabilities.host != expected_host {
        let _ = socket
            .send(Message::Text(
                serialize_wire(&RpcErrorResponse::new(
                    None,
                    ERROR_INVALID_REQUEST,
                    "bridge host mismatch",
                ))
                .into(),
            ))
            .await;
        return;
    }
    let target = target.unwrap_or_else(|| DEFAULT_TARGET.to_owned());
    let key = session_key(expected_host, &target);
    let connection_id = state.next_connection_id();
    let (tx, mut rx) = mpsc::unbounded_channel();
    state.sessions.write().await.insert(
        key.clone(),
        BridgeSessionInfo {
            target,
            capabilities,
            connected_at_epoch_ms: epoch_ms(),
        },
    );
    state.bridge_senders.write().await.insert(
        key.clone(),
        BridgeSender {
            connection_id,
            sender: tx,
        },
    );
    let (mut sender, mut receiver) = socket.split();
    loop {
        tokio::select! {
            Some(outbound) = rx.recv() => {
                if sender.send(Message::Text(serialize_wire(&outbound).into())).await.is_err() { break; }
            }
            Some(message) = receiver.next() => {
                match message {
                    Ok(Message::Text(text)) => handle_bridge_message(&state, &text).await,
                    Ok(Message::Close(_)) => break,
                    _ => {}
                }
            }
            else => break,
        }
    }
    state
        .disconnect_session(&key, connection_id, "bridge disconnected before response")
        .await;
}

async fn handle_bridge_message(state: &BrokerState, text: &str) {
    match serde_json::from_str::<BridgeInbound>(text) {
        Ok(BridgeInbound::Response { mut response }) => {
            if let Some(pending) = state.pending.lock().await.remove(&response.id) {
                response.id = pending.original_id;
                let _ = pending.sender.send(Ok(response));
            }
        }
        Ok(BridgeInbound::Error { mut error }) => {
            if let Some(id) = error.id.clone() {
                if let Some(pending) = state.pending.lock().await.remove(&id) {
                    error.id = Some(pending.original_id);
                    let _ = pending.sender.send(Err(error));
                }
            }
        }
        _ => {}
    }
}

fn validate_request(request: &RpcRequest) -> ValidationResult {
    if request.jsonrpc != JSONRPC_VERSION {
        return Err(Box::new(RpcErrorResponse::new(
            Some(request.id.clone()),
            ERROR_INVALID_REQUEST,
            "unsupported JSON-RPC version",
        )));
    }
    if request.namespace.trim().is_empty() || request.method.trim().is_empty() {
        return Err(Box::new(RpcErrorResponse::new(
            Some(request.id.clone()),
            ERROR_INVALID_REQUEST,
            "request namespace and method must not be empty",
        )));
    }
    Ok(())
}

fn validate_capability_contract(
    request: &RpcRequest,
    target: &str,
    session: &BridgeSessionInfo,
) -> ValidationResult {
    let capabilities = &session.capabilities;
    if capabilities.host != request.host {
        return Err(Box::new(RpcErrorResponse::new(
            Some(request.id.clone()),
            ERROR_CAPABILITY,
            "connected bridge host mismatch",
        )));
    }
    if !capabilities
        .namespaces
        .iter()
        .any(|namespace| namespace == &request.namespace)
    {
        return Err(Box::new(RpcErrorResponse::new(
            Some(request.id.clone()),
            ERROR_CAPABILITY,
            format!(
                "host '{}' target '{}' bridge does not support namespace '{}'",
                request.host, target, request.namespace
            ),
        )));
    }
    if !capabilities
        .methods
        .get(&request.namespace)
        .is_some_and(|methods| methods.iter().any(|method| method == &request.method))
    {
        return Err(Box::new(RpcErrorResponse::new(
            Some(request.id.clone()),
            ERROR_CAPABILITY,
            format!(
                "host '{}' target '{}' bridge does not support method '{}.{}'",
                request.host, target, request.namespace, request.method
            ),
        )));
    }
    Ok(())
}

fn unauthorized_response() -> Response {
    (
        StatusCode::UNAUTHORIZED,
        "invalid or missing x-adobepy-token header",
    )
        .into_response()
}

fn serialize_wire<T: Serialize>(value: &T) -> String {
    serde_json::to_string(value).unwrap_or_else(|_| serialization_error_text(None))
}

fn serialization_error_text(id: Option<&RequestId>) -> String {
    let id_json = id
        .map(|request_id| request_id.to_string())
        .and_then(|value| serde_json::to_string(&value).ok())
        .unwrap_or_else(|| "null".to_owned());
    format!(
        r#"{{"jsonrpc":"{}","id":{},"error":{{"code":{},"message":"failed to serialize broker response"}}}}"#,
        JSONRPC_VERSION, id_json, ERROR_SERIALIZATION
    )
}

fn epoch_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}

#[cfg(test)]
mod tests {
    use super::*;
    use adobepy_protocol::{BridgeKind, Capabilities, RpcOptions};
    use axum::body::Body;
    use axum::http::Request;
    use std::collections::BTreeMap;
    use tower::ServiceExt;

    fn state() -> BrokerState {
        BrokerState::new(&BrokerConfig {
            bind: SocketAddr::from(([127, 0, 0, 1], 0)),
            token: "t".into(),
            default_timeout_ms: 1,
        })
    }

    fn request() -> RpcRequest {
        RpcRequest {
            jsonrpc: JSONRPC_VERSION.into(),
            id: RequestId::from_string("x"),
            host: HostKind::Photoshop,
            target: Some(DEFAULT_TARGET.into()),
            namespace: "app".into(),
            method: "getVersion".into(),
            args: vec![],
            options: RpcOptions::default(),
        }
    }

    fn caps() -> Capabilities {
        let mut methods = BTreeMap::new();
        methods.insert("app".into(), vec!["getVersion".into()]);
        Capabilities {
            host: HostKind::Photoshop,
            bridge_kind: BridgeKind::Uxp,
            bridge_version: "0.1.0".into(),
            host_version: None,
            namespaces: vec!["app".into()],
            features: vec![],
            methods,
        }
    }

    #[tokio::test]
    async fn endpoints_and_dispatch_errors() {
        let app = broker_router(state());
        let response = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/health")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/v1/capabilities")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        let state = state();
        let error = state.dispatch_request(request()).await.unwrap_err();
        assert_eq!(error.error.code, ERROR_BRIDGE_NOT_INSTALLED);

        let mut invalid = request();
        invalid.jsonrpc = "1.0".into();
        let error = state.dispatch_request(invalid).await.unwrap_err();
        assert_eq!(error.error.code, ERROR_INVALID_REQUEST);
    }

    #[tokio::test]
    async fn dispatch_roundtrip_restores_id() {
        let state = state();
        let key = session_key(HostKind::Photoshop, DEFAULT_TARGET);
        let (tx, mut rx) = mpsc::unbounded_channel();
        state.bridge_senders.write().await.insert(
            key.clone(),
            BridgeSender {
                connection_id: 1,
                sender: tx,
            },
        );
        state.sessions.write().await.insert(
            key,
            BridgeSessionInfo {
                target: DEFAULT_TARGET.into(),
                capabilities: caps(),
                connected_at_epoch_ms: 1,
            },
        );
        let s = state.clone();
        let task = tokio::spawn(async move { s.dispatch_request(request()).await });
        let BridgeOutbound::Request { request } = rx.recv().await.unwrap();
        handle_bridge_message(
            &state,
            &serde_json::to_string(&BridgeInbound::Response {
                response: RpcResponse {
                    jsonrpc: JSONRPC_VERSION.into(),
                    id: request.id,
                    result: json!("ok"),
                    diagnostics: None,
                },
            })
            .unwrap(),
        )
        .await;
        assert_eq!(task.await.unwrap().unwrap().id, RequestId::from_string("x"));
    }

    #[tokio::test]
    async fn dispatch_enforces_capabilities_and_timeout() {
        let state = state();
        let key = session_key(HostKind::Photoshop, DEFAULT_TARGET);
        let (tx, mut rx) = mpsc::unbounded_channel();
        state.bridge_senders.write().await.insert(
            key.clone(),
            BridgeSender {
                connection_id: 1,
                sender: tx,
            },
        );
        state.sessions.write().await.insert(
            key,
            BridgeSessionInfo {
                target: DEFAULT_TARGET.into(),
                capabilities: caps(),
                connected_at_epoch_ms: 1,
            },
        );

        let mut missing = request();
        missing.method = "missing".into();
        let error = state.dispatch_request(missing).await.unwrap_err();
        assert_eq!(error.error.code, ERROR_CAPABILITY);

        let task = tokio::spawn({
            let state = state.clone();
            async move { state.dispatch_request(request()).await }
        });
        assert!(matches!(
            rx.recv().await.unwrap(),
            BridgeOutbound::Request { .. }
        ));
        let error = task.await.unwrap().unwrap_err();
        assert_eq!(error.error.code, ERROR_TIMEOUT);
    }

    #[tokio::test]
    async fn disconnect_drains_pending_requests_for_current_connection() {
        let state = state();
        let key = session_key(HostKind::Photoshop, DEFAULT_TARGET);
        let (tx, mut rx) = mpsc::unbounded_channel();
        state.bridge_senders.write().await.insert(
            key.clone(),
            BridgeSender {
                connection_id: 7,
                sender: tx,
            },
        );
        state.sessions.write().await.insert(
            key.clone(),
            BridgeSessionInfo {
                target: DEFAULT_TARGET.into(),
                capabilities: caps(),
                connected_at_epoch_ms: 1,
            },
        );
        let task = tokio::spawn({
            let state = state.clone();
            async move { state.dispatch_request(request()).await }
        });
        assert!(matches!(
            rx.recv().await.unwrap(),
            BridgeOutbound::Request { .. }
        ));
        state.disconnect_session(&key, 7, "bridge closed").await;
        let error = task.await.unwrap().unwrap_err();
        assert_eq!(error.error.code, ERROR_BRIDGE_NOT_INSTALLED);
        assert_eq!(state.sessions.read().await.len(), 0);
    }
}
