import * as fs from 'fs';
import * as path from 'path';

export class WebviewManager {
    private static instance: WebviewManager;
    
    private constructor() {}

    static getInstance(): WebviewManager {
        if (!WebviewManager.instance) {
            WebviewManager.instance = new WebviewManager();
        }
        return WebviewManager.instance;
    }

    getWebviewContent(extensionPath: string): string {
        const htmlPath = path.join(extensionPath, 'src', 'webview', 'index.html');
        const cssPath = path.join(extensionPath, 'src', 'webview', 'styles.css');
        const jsPath = path.join(extensionPath, 'src', 'webview', 'script.js');

        let html = fs.readFileSync(htmlPath, 'utf-8');
        const css = fs.readFileSync(cssPath, 'utf-8');
        const js = fs.readFileSync(jsPath, 'utf-8');

        // Add CSP meta tag for security
        const csp = `
            <meta http-equiv="Content-Security-Policy" 
                  content="default-src 'none'; 
                          style-src 'unsafe-inline'; 
                          script-src 'unsafe-inline' 'unsafe-eval';
                          img-src vscode-resource: https:">
        `;

        // Insert CSP, CSS, and JavaScript into HTML
        html = html.replace('</head>', `${csp}<style>${css}</style></head>`);
        html = html.replace('</body>', `
            <script>
                const vscode = acquireVsCodeApi();
            </script>
            <script>${js}</script>
        </body>`);

        return html;
    }
}