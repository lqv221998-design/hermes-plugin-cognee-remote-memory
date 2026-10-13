# Kiểm thử bản nguồn

Dùng venv test riêng, không sửa môi trường production Hermes. Runtime client chỉ cần Hermes và FastAPI khai báo; dependencies dưới đây chỉ cho tests.

- Cài pytest, fastapi, uvicorn, httpx và playwright trong venv test; browser fixture hiện được kiểm bằng Edge trên Windows. Browser fixture không phải Cognee thật/Electron.
- UI test adapter cần React/ReactDOM/esbuild trong thư mục npm test riêng. Chạy `node tests/ui/build.mjs <repo-root> <node-test-root>` để tạo evidence/ui-fixture-bundle.js. Plugin production không cần build/npm.
- Chạy `python -m pytest -c tests/pytest.ini tests -q`. Root package dùng relative imports; giữ config importlib và test pythonpath, không để pytest import root như module __init__ trống package.
- Actual routing: `python tests/native_memory_tools.py --hermes-repo <installed-Hermes-checkout>` bằng interpreter Hermes.
- Native doctor: `hermes plugins doctor <absolute-source-directory> --ci`; validator: `hermes plugins validate <absolute-source-directory> --json`. Không suy UI/native Git install từ Doctor pass.
- Native Electron: cung cấp HERMES_NATIVE_PLUGIN_DETECTOR đường dẫn installed electron/desktop-plugin-install.ts, HERMES_TEST_GIT binary host và TMPDIR scratch. Chạy Node với tsx loader installed host để gọi tests/test_native_install.mjs; module test real probe/install vào target mới, force=false và byte comparison/no-overwrite. Không chạm profile thật.
- Bốn upstream suites: test_http_backend.py, test_lifecycle_contract.py, test_layered_recall.py, test_tool_contract.py trong upstream/tests, PYTHONPATH là root repo. Snapshot upstream giữ nguyên hash; warning pending async task upstream phải báo riêng.

Các log/screenshot/runtime temp dưới evidence hoặc managed scratch không đưa lên GitHub. Kiểm downloaded source/release full file set/hash, Git autocrlf=true, separate native Agent install và Desktop install. Physical recipient, actual HTTPS/ACL/new-session memory và chi phí/semantic quality là acceptance riêng.
