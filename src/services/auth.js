export const login = async (email) => {
  // Mock login since backend doesn't have auth yet
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockToken = 'mock-jwt-token-12345';
      const mockUser = { email, name: 'Demo User' };
      localStorage.setItem('med_token', mockToken);
      localStorage.setItem('med_user', JSON.stringify(mockUser));
      resolve({ token: mockToken, user: mockUser });
    }, 500);
  });
};

export const register = async (name, email) => {
  // Mock register
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockToken = 'mock-jwt-token-12345';
      const mockUser = { email, name };
      localStorage.setItem('med_token', mockToken);
      localStorage.setItem('med_user', JSON.stringify(mockUser));
      resolve({ token: mockToken, user: mockUser });
    }, 500);
  });
};

export const logout = () => {
  localStorage.removeItem('med_token');
  localStorage.removeItem('med_user');
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('med_user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('med_token');
};
