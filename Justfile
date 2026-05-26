set shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

default:
    just --list

test:
    npm run test:all

quick:
    npm run test:quick

bridges:
    npm run test:bridges

lint:
    cargo fmt --check
    cargo clippy --workspace --all-targets -- -D warnings

build:
    cargo build --release -p adobepy-cli --bin adobepy
    npm run uxp:build
    npm run cep:build

package:
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/package-release.ps1

package-quick:
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/package-release.ps1 -SkipTests
