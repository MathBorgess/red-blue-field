import os
import shutil
import socket
import threading
import time

import pytest
import uvicorn

from red_blue_field.api import create_app
from red_blue_field.config import Settings

pytestmark = pytest.mark.skipif(os.getenv('RBF_TEST_BROWSER') != '1', reason='Set RBF_TEST_BROWSER=1 with Chromium installed')


def test_operator_can_run_compare_and_assess_in_browser(tmp_path):
    from playwright.sync_api import sync_playwright
    app = create_app(Settings(data_dir=tmp_path, control_token='browser-control-token-' + 'x' * 24))
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(.02)
    assert server.started
    try:
        with sync_playwright() as p:
            executable = os.getenv('RBF_CHROMIUM') or shutil.which('chromium')
            browser = p.chromium.launch(executable_path=executable, headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{port}')
            page.locator('#token').fill(app.state.lab.settings.control_token)
            page.locator('#connect button').click()
            page.locator('#workspace').wait_for(state='visible')
            page.locator('#profile').select_option('A')
            page.locator('#new-run button').click()
            page.locator('#episode').wait_for(state='visible')
            page.locator('#start').click()
            page.wait_for_function("() => document.getElementById('status').textContent === 'complete'")
            assert 'attacker_success' in page.locator('#metrics').inner_text()
            page.locator('[data-tab="hypotheses"]').click()
            page.wait_for_selector('.node')
            assert page.locator('.node').count() == 3
            page.locator('[data-tab="state"]').click()
            page.wait_for_function("() => document.getElementById('snapshot').textContent.includes('cross_tenant_read')")
            with page.expect_download() as downloaded:
                page.locator('#export').click()
            assert downloaded.value.suggested_filename.endswith('.zip')
            page.locator('[data-tab="assessment"]').click()
            page.locator('#explanation').fill('O servidor do perfil A aceitou acesso ao ticket de outro cliente. A evidência registra esse efeito.')
            page.locator('#assessment-form button').click()
            page.wait_for_function("() => document.getElementById('assessments').textContent.includes('guided')")
            assert page.evaluate('Object.keys(localStorage).length') == 0
            assert page.evaluate('Object.keys(sessionStorage).length') == 0
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert errors == []
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)
