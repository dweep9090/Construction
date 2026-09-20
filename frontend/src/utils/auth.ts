export function parseJwt(token: string) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export function getCurrentUser() {
  const token = localStorage.getItem('token');
  if (!token) return null;
  const decoded = parseJwt(token);
  if (!decoded) return null;
  return {
    id: decoded.sub,
    role: decoded.role,
    name: decoded.name || 'User'
  };
}
