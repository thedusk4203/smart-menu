# ADR-0001 — Modular monolith và dependency layering

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: backend/frontend architecture

## Context

Code hiện tổ chức FastAPI theo `modules/<feature>` và React theo route/page/API wrapper. `dependencies.py` là composition root; database vẫn là một PostgreSQL schema.

## Decision

Giữ modular monolith: router/schema → use case/domain/port → repository/provider. Frontend page gọi API wrapper thay vì persistence trực tiếp.

## Consequences

Module mới phải giữ dependency direction và đăng ký router/factory. Không tách microservice nếu chưa có boundary vận hành độc lập.

## Verification and revisit trigger

Kiểm `api.py`, `dependencies.py`, module tests và route/API map. Xem lại khi một module cần deploy, scale hoặc ownership độc lập.

