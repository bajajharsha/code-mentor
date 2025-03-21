import axios, { AxiosInstance } from 'axios';
import * as fs from 'fs';
import { log } from 'node:console';
import * as vscode from 'vscode';

export interface AuthResult {
    token?: string;
    user?: {
        email: string;
        id: string;
    };
    [key: string]: any;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export class ApiService {
    private client: AxiosInstance;
    public token: string | null = null;
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext, baseURL: string = 'http://127.0.0.1:8000/api/v1') {
        this.context = context;
        this.client = axios.create({
            baseURL,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async init() {
        await this.restoreToken();
    }

    async setToken(token: string) {
        log("Token set: ", token);
        this.token = token;
        this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        // console.log("Token set in client headers.");
        

        // Securely store the token
        await this.context.secrets.store("authToken", token);
        console.log("Token stored securely in context secrets.");
    }
    
    async validateToken(): Promise<boolean> {
        if (!this.token) {
            return false;
        }

        try {
            const response = await this.client.get('/auth/users/me');
            console.log("DEV-CHECK ::: Token validation response: *************", response.data);
            
            return response.status === 200;
        } catch (error) {
            console.error("DEV-CHECK ::: Token validation failed:", error);

            const refreshed = await this.refreshToken();
            if (refreshed) {
                return true;
            }
            
            await this.clearToken(); // Clear invalid token
            console.log("DEV-CHECK ::: Token cleared after validation failure.");
            
            return false;
        }
    }

    async refreshToken(): Promise<boolean> {
    try {
        const response = await this.client.post('/auth/refresh-token');
        if (response.data.access_token) {
            await this.setToken(response.data.access_token);
            return true;
        }
        return false;
    } catch (error) {
        console.error("Token refresh failed:", error);
        return false;
    }
}

    async restoreToken() {
        const storedToken = await this.context.secrets.get("authToken");
        console.log("DEV-CHECK ::: Restoring token from storage...", storedToken);

        if (storedToken) {
            this.token = storedToken;
            this.client.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
            
            // Validate the token
            const isValid = await this.validateToken();
            if (!isValid) {
                console.log("Stored token is invalid, clearing...");
                await this.clearToken();
                console.log("DEV-CHECK ::: Token cleared after validation failure. 222222");
                
                return false;
            }
            return true;
        }
        return false;
    }

    async clearToken() {
        this.token = null;
        delete this.client.defaults.headers.common['Authorization'];
        await this.context.secrets.delete("authToken");
        console.log("Token cleared from storage.");
    }

    async register(email: string, password: string): Promise<AuthResult> {
        const payload = { email, password };
        const endpoint = '/auth/register';
        log("Registering user...", email, password);
        const response = await this.post(payload, endpoint);
        if (response.data.access_token) {
            await this.setToken(response.data.access_token);
        }
        return response;
    }

    async login(email: string, password: string): Promise<AuthResult> {
        const payload = { email, password };
        const endpoint = '/auth/login';
        log("Login user...", email, password);
        const response = await this.post(payload, endpoint);
        if (response.access_token) {
            await this.setToken(response.access_token);
        }
        return response;
    }

    async post(payload: any, endpoint: string): Promise<AuthResult> {
        try {
            const response = await this.client.post(endpoint, payload);
            
            console.log("Response data: for endpoint ",endpoint, response.data);
            // return response.data if data exists
            return response?.data || response;
        } catch (error) {
            const err = error as any;
            console.log("Error response:", err.response?.data);
            throw err.response?.data || 'Authentication failed';
        }
    }

    async resyncIndex(chunksPath: string, firstFlag: boolean, email: string, workspaceName: string): Promise<any> {
        try {
            const formData = new FormData();
            const chunksFile = await fs.promises.readFile(chunksPath);
            
            // Make sure the file has the correct name as expected by your backend
            formData.append('file', new Blob([chunksFile]), 'chunks.json'); // Use 'file' as the key if that's what your API expects
            
            formData.append('is_first_time', firstFlag.toString());
            formData.append('email', email);
            formData.append('filepath', workspaceName); // Ensure field name matches backend expectation
            
            // Preserve the Authorization header while setting multipart/form-data
            const response = await this.client.post('/resync-index', formData, {
                headers: {
                    ...this.client.defaults.headers.common, // Preserve Authorization header
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        } catch (error) {
            console.error("Error syncing index:", error);
            throw error;
        }
    }

    async query(payload: any): Promise<any> {
        console.log("Querying...", payload);

        try {
            const endpoint = '/query';
            const response = await this.post(payload, endpoint);   
            return response.data.response;
        } catch (error) {
            console.error("Query failed:", error);
            // throw error;
        }
    }

    async modifiedFile(payload: any): Promise<any> {
        try {
            console.log("Modified file...", payload);
            const endpoint = '/llm-rewrite';
            const response = await this.post(payload, endpoint);
            console.log("Modified file response: ", response);
            
            return response.data;
        } catch (error) {
            console.error("Modified file failed:", error);
            throw error;
        }
    }
}