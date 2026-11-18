function checkAuth() {
  if (!localStorage.getItem('weather_token')) {
    window.location.href = '../login.html';
  }
}

function getUserInfo() {
  const u = localStorage.getItem('weather_user');
  return u ? JSON.parse(u) : null;
}

function isAdmin() {
  const u = getUserInfo();
  return u && u.role === 'admin';
}
