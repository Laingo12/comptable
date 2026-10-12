import { apiClient, rawClient } from '@/lib/apiClient';
import type { components } from '@/types/api';

export type UserRead = components['schemas']['UserRead'];
export type TokenPair = components['schemas']['TokenPair'];
export type AccessToken = components['schemas']['AccessToken'];

export interface LoginInput { username: string; password: string }

export const authApi = {
  async login(input: LoginInput): Promise<TokenPair> {
    const { data } = await rawClient.post<TokenPair>('/auth/login', input);
    return data;
  },
  async logout(refresh_token: string): Promise<void> {
    await apiClient.post('/auth/logout', { refresh_token });
  },
  async me(): Promise<UserRead> {
    const { data } = await apiClient.get<UserRead>('/auth/me');
    return data;
  },
};