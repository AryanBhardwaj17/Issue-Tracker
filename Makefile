.PHONY: proto-gen

# ── Proto stub generation ─────────────────────────────────────────────────────
# Compiles proto/user_lookup.proto into Python gRPC stubs for both Auth and
# Core services.  Requires grpcio-tools (pip install grpcio-tools).

PROTO_SRC  = proto/user_lookup.proto
AUTH_OUT   = services/auth/app/generated
CORE_OUT   = services/core/app/generated

proto-gen:
	@echo "Generating gRPC stubs..."
	python -m grpc_tools.protoc \
		-Iproto \
		--python_out=$(AUTH_OUT) \
		--grpc_python_out=$(AUTH_OUT) \
		$(PROTO_SRC)
	python -m grpc_tools.protoc \
		-Iproto \
		--python_out=$(CORE_OUT) \
		--grpc_python_out=$(CORE_OUT) \
		$(PROTO_SRC)
	@echo "Fixing imports in generated stubs..."
	python -c "import pathlib; \
		[f.write_text(f.read_text().replace('import user_lookup_pb2', 'from app.generated import user_lookup_pb2')) \
		 for f in [pathlib.Path('$(AUTH_OUT)/user_lookup_pb2_grpc.py'), pathlib.Path('$(CORE_OUT)/user_lookup_pb2_grpc.py')]]"
	@echo "Done."
