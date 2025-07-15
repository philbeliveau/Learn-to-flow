/**
 * Enhanced Authentication Service with JWT, MFA, and Role-Based Access
 * Security Engineer Integration: JWT tokens, MFA, RBAC
 * Performance Engineer Integration: Redis caching, optimized responses
 */

import { jwtDecode } from 'jwt-decode';

// API Configuration - Use authentication server on port 8004
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
const REFRESH_TOKEN_KEY = 'refresh_token';
const ACCESS_TOKEN_KEY = 'access_token';
const USER_DATA_KEY = 'user_data';
const MFA_SECRET_KEY = 'mfa_secret';

// User roles for RBAC
export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  ANALYST = 'analyst',
  VIEWER = 'viewer'
}

// User permissions
export enum Permission {
  READ_DASHBOARD = 'read_dashboard',
  WRITE_DASHBOARD = 'write_dashboard',
  READ_ANALYTICS = 'read_analytics',
  WRITE_ANALYTICS = 'write_analytics',
  READ_MANUFACTURING = 'read_manufacturing',
  WRITE_MANUFACTURING = 'write_manufacturing',
  READ_FINANCE = 'read_finance',
  WRITE_FINANCE = 'write_finance',
  USER_MANAGEMENT = 'user_management',
  SYSTEM_ADMIN = 'system_admin'
}

// Role-based permissions mapping
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.ADMIN]: [
    Permission.READ_DASHBOARD,
    Permission.WRITE_DASHBOARD,
    Permission.READ_ANALYTICS,
    Permission.WRITE_ANALYTICS,
    Permission.READ_MANUFACTURING,
    Permission.WRITE_MANUFACTURING,
    Permission.READ_FINANCE,
    Permission.WRITE_FINANCE,
    Permission.USER_MANAGEMENT,
    Permission.SYSTEM_ADMIN
  ],
  [UserRole.MANAGER]: [
    Permission.READ_DASHBOARD,
    Permission.WRITE_DASHBOARD,
    Permission.READ_ANALYTICS,
    Permission.WRITE_ANALYTICS,
    Permission.READ_MANUFACTURING,
    Permission.WRITE_MANUFACTURING,
    Permission.READ_FINANCE,
    Permission.WRITE_FINANCE
  ],
  [UserRole.ANALYST]: [
    Permission.READ_DASHBOARD,
    Permission.READ_ANALYTICS,
    Permission.WRITE_ANALYTICS,
    Permission.READ_MANUFACTURING,
    Permission.READ_FINANCE
  ],
  [UserRole.VIEWER]: [
    Permission.READ_DASHBOARD,
    Permission.READ_ANALYTICS,
    Permission.READ_MANUFACTURING,
    Permission.READ_FINANCE
  ]
};

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  permissions: Permission[];
  company?: {
    id: string;
    name: string;
  };
  is_mfa_enabled: boolean;
  last_login?: string;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  mfa_code?: string;
}

export interface MFASetupData {
  secret: string;
  qr_code: string;
  backup_codes: string[];
}

export interface AuthResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  user?: User;
  requires_mfa?: boolean;
  mfa_setup?: MFASetupData;
  message?: string;
}

export interface TokenPayload {
  user_id: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
  exp: number;
  iat: number;
}

export class AuthService {
  private static instance: AuthService;
  private tokenRefreshTimer: NodeJS.Timeout | null = null;
  private user: User | null = null;

  private constructor() {
    // Initialize user data if tokens exist
    this.initializeFromStorage();
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Initialize authentication state from localStorage
   */
  private initializeFromStorage(): void {
    // Skip initialization during SSR
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      const userData = localStorage.getItem(USER_DATA_KEY);
      
      if (accessToken && userData) {
        const user = JSON.parse(userData);
        if (this.isTokenValid(accessToken)) {
          this.user = user;
          this.scheduleTokenRefresh();
        } else {
          this.clearAuthData();
        }
      }
    } catch (error) {
      console.error('Failed to initialize from storage:', error);
      this.clearAuthData();
    }
  }

  /**
   * Login with email and password
   */
  public async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Handle simple auth service response format
      if (data.access_token && data.user) {
        // Store tokens and user data (only in browser)
        if (typeof window !== 'undefined') {
          localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
          // No refresh token in simple auth service
        }
        
        // Enhanced user data with permissions
        const enhancedUser = {
          ...data.user,
          permissions: ROLE_PERMISSIONS[data.user.role as UserRole] || []
        };
        
        if (typeof window !== 'undefined') {
          localStorage.setItem(USER_DATA_KEY, JSON.stringify(enhancedUser));
        }
        
        this.user = enhancedUser;
        this.scheduleTokenRefresh();
        
        return { 
          success: true,
          access_token: data.access_token,
          user: enhancedUser
        };
      }

      return {
        success: false,
        message: 'Invalid response format'
      };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Login failed'
      };
    }
  }

  /**
   * Setup Multi-Factor Authentication
   */
  public async setupMFA(): Promise<MFASetupData | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/mfa/setup`, {
        method: 'POST',
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('MFA setup failed');
      }

      const data = await response.json();
      
      if (data.success) {
        // Store MFA secret temporarily for verification (only in browser)
        if (typeof window !== 'undefined') {
          localStorage.setItem(MFA_SECRET_KEY, data.secret);
        }
        return data;
      }

      return null;
    } catch (error) {
      console.error('MFA setup error:', error);
      return null;
    }
  }

  /**
   * Verify MFA setup
   */
  public async verifyMFA(code: string): Promise<boolean> {
    try {
      if (typeof window === 'undefined') {
        return false;
      }
      
      const secret = localStorage.getItem(MFA_SECRET_KEY);
      if (!secret) {
        return false;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/mfa/verify`, {
        method: 'POST',
        headers: await this.getAuthHeaders(),
        body: JSON.stringify({ code, secret })
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      
      if (data.success) {
        // Clear temporary secret (only in browser)
        if (typeof window !== 'undefined') {
          localStorage.removeItem(MFA_SECRET_KEY);
          // Update user MFA status
          if (this.user) {
            this.user.is_mfa_enabled = true;
            localStorage.setItem(USER_DATA_KEY, JSON.stringify(this.user));
          }
        }
        return true;
      }

      return false;
    } catch (error) {
      console.error('MFA verification error:', error);
      return false;
    }
  }

  /**
   * Refresh access token using refresh token
   */
  public async refreshToken(): Promise<boolean> {
    try {
      if (typeof window === 'undefined') {
        return false;
      }
      
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      if (!response.ok) {
        this.clearAuthData();
        return false;
      }

      const data = await response.json();
      
      if (data.success && data.access_token) {
        if (typeof window !== 'undefined') {
          localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
        }
        this.scheduleTokenRefresh();
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearAuthData();
      return false;
    }
  }

  /**
   * Logout user
   */
  public async logout(): Promise<void> {
    try {
      if (typeof window === 'undefined') {
        this.clearAuthData();
        return;
      }
      
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (refreshToken) {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${refreshToken}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearAuthData();
    }
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    return token !== null && this.isTokenValid(token) && this.user !== null;
  }

  /**
   * Get current user
   */
  public getCurrentUser(): User | null {
    return this.user;
  }

  /**
   * Check if user has specific permission
   */
  public hasPermission(permission: Permission): boolean {
    return this.user?.permissions.includes(permission) || false;
  }

  /**
   * Check if user has any of the specified permissions
   */
  public hasAnyPermission(permissions: Permission[]): boolean {
    return permissions.some(permission => this.hasPermission(permission));
  }

  /**
   * Check if user has specific role
   */
  public hasRole(role: UserRole): boolean {
    return this.user?.role === role;
  }

  /**
   * Check if user has any of the specified roles
   */
  public hasAnyRole(roles: UserRole[]): boolean {
    return roles.some(role => this.hasRole(role));
  }

  /**
   * Get authentication headers for API requests
   */
  public async getAuthHeaders(): Promise<HeadersInit> {
    if (typeof window === 'undefined') {
      throw new Error('Authentication required');
    }
    
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    
    if (!token || !this.isTokenValid(token)) {
      const refreshed = await this.refreshToken();
      if (!refreshed) {
        throw new Error('Authentication required');
      }
    }

    return {
      'Authorization': `Bearer ${localStorage.getItem(ACCESS_TOKEN_KEY)}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Get cached user data with Redis optimization
   */
  public async getCachedUserData(): Promise<User | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/user`, {
        headers: await this.getAuthHeaders()
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      
      if (data.success && data.user) {
        const enhancedUser = {
          ...data.user,
          permissions: ROLE_PERMISSIONS[data.user.role as UserRole] || []
        };
        
        this.user = enhancedUser;
        if (typeof window !== 'undefined') {
          localStorage.setItem(USER_DATA_KEY, JSON.stringify(enhancedUser));
        }
        return enhancedUser;
      }

      return null;
    } catch (error) {
      console.error('Failed to get cached user data:', error);
      return null;
    }
  }

  /**
   * Validate token expiry
   */
  private isTokenValid(token: string): boolean {
    try {
      const payload = jwtDecode<TokenPayload>(token);
      const now = Date.now() / 1000;
      return payload.exp > now;
    } catch (error) {
      return false;
    }
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
    }

    if (typeof window === 'undefined') {
      return;
    }
    
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) return;

    try {
      const payload = jwtDecode<TokenPayload>(token);
      const now = Date.now() / 1000;
      const timeUntilExpiry = payload.exp - now;
      
      // Refresh token 5 minutes before expiry
      const refreshTime = Math.max(timeUntilExpiry - 300, 60) * 1000;
      
      this.tokenRefreshTimer = setTimeout(() => {
        this.refreshToken();
      }, refreshTime);
    } catch (error) {
      console.error('Failed to schedule token refresh:', error);
    }
  }

  /**
   * Clear all authentication data
   */
  private clearAuthData(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);
      localStorage.removeItem(MFA_SECRET_KEY);
    }
    
    this.user = null;
    
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }
}

// Export singleton instance
export const authService = AuthService.getInstance();