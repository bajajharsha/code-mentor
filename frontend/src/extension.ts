import * as Diff from 'diff';
import * as vscode from "vscode";
import { ApiService } from "./services/api";
import { WebviewManager } from './webview/webviewManager';

import { generateCodeChunks } from './backend';
class ChatViewProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;
  private apiService: ApiService;

  constructor(private readonly extensionUri: vscode.Uri, private readonly context: vscode.ExtensionContext) {
    this.apiService = new ApiService(context);
}

  public async resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    token: vscode.CancellationToken
  ) {
    console.log("Resolving webview...");
    
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };
    webviewView.webview.html = WebviewManager.getInstance().getWebviewContent(this.extensionUri.fsPath);
    // webviewView.webview.html = getWebviewContent();
    console.log("Webview resolved -----------");

    // Handle messages from webview
    webviewView.webview.onDidReceiveMessage(async (message) => {
      console.log("DEV-CHECK ::: Received message: ", message);
      switch (message.command) {
        case "checkSession":
          await this.restoreSession(webviewView);
          break;

        case "register":
          try {
            console.log("DEV-CHECK ::: Registering user...", message.email, message.password);
            
            const result = await this.apiService.register(message.email, message.password);
            webviewView.webview.postMessage({ 
              command: 'authResult', 
              success: true,
              data: result 
            });
          } catch (error) {
            webviewView.webview.postMessage({ 
              command: 'authResult', 
              success: false, 
              error: error instanceof Error ? error.message : 'Authentication failed'
            });
          }
          break;
        
        case "login":
          try {
            console.log("Logging user...", message.email, message.password);
            
            const result = await this.apiService.login(message.email, message.password);
            webviewView.webview.postMessage({ 
              command: 'authResult', 
              success: true,
              data: result 
            });
          } catch (error) {
            webviewView.webview.postMessage({ 
              command: 'authResult', 
              success: false, 
              error: error instanceof Error ? error.message : 'Authentication failed'
            });
          }
          break;

        case "indexCodebase":
          try {
            const result = await generateCodeChunks(message.email, message.firstFlag);
            const { chunksPath, workspaceName, email, firstFlag } = result as any;

            console.log("chunksPath: ", chunksPath);
            console.log("workspaceName: ", workspaceName);
            console.log("email: ", email);
            console.log("firstFlag: ", firstFlag);
            

            // Call the resync API
            await this.apiService.resyncIndex(chunksPath, firstFlag, email, workspaceName);
            
            webviewView.webview.postMessage({
                command: 'indexingComplete',
                success: true
            });
          } catch (error) {
            console.error("Error during indexing:", error);
            webviewView.webview.postMessage({
                command: 'indexingComplete',
                success: false,
                error: error instanceof Error ? error.message : 'Indexing failed'
            });
          }
          break;

        case "logout":
          console.log("Logging out...");
          await this.apiService.clearToken();
          break;
      
        case "getActiveFileDetails":
          console.log("Getting active file details...");
          const activeEditor = vscode.window.activeTextEditor;
          if (activeEditor) {
            const document = activeEditor.document;
            const content = document.getText();
            const filePath = document.uri.fsPath;
            const workspaceName = vscode.workspace.name || 'default';

            try {
                const response = await this.apiService.query({
                    user_query: message.text,
                    current_file_content: content || "Null",
                    current_file_path: filePath,
                    email: message.email,
                    workspace_name: workspaceName
                });

                // Make sure we're calling the method correctly
                const modifiedFileResponse = await this.apiService.modifiedFile({
                    orignal_file: content,
                    rewritten_code: response
                });

                // Extract content from <code> tags if they exist
                let processedResponse = modifiedFileResponse;
                if (modifiedFileResponse && typeof modifiedFileResponse === "string") {
                    const codeRegex = /<code>([\s\S]*?)<\/code>/g;
                    const matches = [...modifiedFileResponse.matchAll(codeRegex)];
                    
                    if (matches.length > 0) {
                        // Extract the content from the matches
                        processedResponse = matches.map(match => match[1]).join('\n');
                        console.log("Extracted code from <code> tags");
                    }
                }

                // Check if we have a valid response before showing diff
                if (processedResponse && typeof processedResponse === "string") {
                    await showDiff(content, processedResponse);
                } else {
                    console.error("Modified file response is invalid:", modifiedFileResponse);
                }

                // Send response to webview
                if (this._view) {
                    this._view.webview.postMessage({
                        command: 'answerResult',
                        answer: response
                    });
                }
            } catch (error) {
                console.error("Error in getActiveFileDetails:", error);
                // You might want to show an error message to the user here
                if (this._view) {
                    this._view.webview.postMessage({
                        command: 'error',
                        message: 'Failed to process file'
                    });
                }
            }
          }
          break;
      }
    });

    // handle authenticate
    
  }

  private async handleAuthenticate(webviewView: vscode.WebviewView, message: any) {
    try {
      const result = await this.apiService.register(message.email, message.password);
      webviewView.webview.postMessage({ 
        command: 'authResult', 
        success: true,
        data: result 
      });
    } catch (error) {
      webviewView.webview.postMessage({ 
        command: 'authResult', 
        success: false, 
        error: error instanceof Error ? error.message : 'Authentication failed'
      });
    }
  }

  private async restoreSession(webviewView: vscode.WebviewView) {
    try {
        console.log("DEV-CHECK ::: Restoring session...");
        
        await this.apiService.init();
        const isValid = await this.apiService.validateToken();

        webviewView.webview.postMessage({ 
            command: "sessionRestored", 
            success: isValid,
            error: isValid ? null : "Session expired or invalid"
        });
    } catch (error) {
        console.error("Error restoring session:", error);
        webviewView.webview.postMessage({ 
            command: "sessionRestored", 
            success: false, 
            error: "Failed to restore session" 
        });
    }
  }
}

export function activate(context: vscode.ExtensionContext) {
  const provider = new ChatViewProvider(context.extensionUri, context);
  
  // Register the provider with a consistent ID
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codeAssistChatView", provider)
  );
  console.log("Congratulations, your extension 'code-assist-chat' is now active!");
  
  // Use the same ID in your command
  let disposable = vscode.commands.registerCommand("codeAssistChat.startChat", async () => {
    await vscode.commands.executeCommand("codeAssistChatView.focus");
  });
  console.log("====================================");
  
  context.subscriptions.push(disposable);
}

export async function showDiff(originalContent: string, modifiedContent: string) {
    try{
      const originalUri = vscode.Uri.parse('untitled:OriginalFile');
      const modifiedUri = vscode.Uri.parse('untitled:ModifiedFile');
  
      // Create a text document with the original content
      const originalDoc = await vscode.workspace.openTextDocument(originalUri);
      const edit = new vscode.WorkspaceEdit();
      edit.insert(originalUri, new vscode.Position(0, 0), originalContent);
      await vscode.workspace.applyEdit(edit);
  
      // Create a text document with the modified content
      const modifiedDoc = await vscode.workspace.openTextDocument(modifiedUri);
      const edit2 = new vscode.WorkspaceEdit();
      edit2.insert(modifiedUri, new vscode.Position(0, 0), modifiedContent);
      await vscode.workspace.applyEdit(edit2);
  
      // Open the VS Code diff view
      await vscode.commands.executeCommand('vscode.diff', originalUri, modifiedUri, 'Code Suggestions');
    } catch (error) {
      console.error("Error showing diff:", error);
    }
}
export async function showCustomDiff(originalContent: string, modifiedContent: string) {
    const panel = vscode.window.createWebviewPanel(
        "customDiffView",
        "Code Diff View",
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );
    const diffResult = Diff.diffLines(originalContent, modifiedContent);
    let diffHtml = `<html><head><style>
        body { font-family: monospace; padding: 10px; background: #282C34; color: white; }
        .diff-container { border: 1px solid #444; padding: 10px; border-radius: 5px; }
        .added { background: #144212; color: #A6E22E; padding: 2px 5px; display: block; }
        .removed { background: #420E09; color: #F92672; padding: 2px 5px; display: block; }
        .unchanged { color: #ddd; padding: 2px 5px; display: block; }
    </style></head><body>`;
    diffHtml += `<div class="diff-container">`;
    diffResult.forEach((part) => {
        if (part.added) {
            diffHtml += `<div class="added">+ ${part.value}</div>`;
        } else if (part.removed) {
            diffHtml += `<div class="removed">- ${part.value}</div>`;
        } else {
            diffHtml += `<div class="unchanged">${part.value}</div>`;
        }
    });
    diffHtml += `</div></body></html>`;
    panel.webview.html = diffHtml;
}


export function deactivate() {}
