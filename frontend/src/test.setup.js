// Test setup: provide robust localStorage/sessionStorage mocks when jsdom isn't sufficient.

function createStorageMock() {
  let store = {};
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key)
        ? store[key]
        : null;
    },
    setItem(key, value) {
      store[key] = String(value);
    },
    removeItem(key) {
      delete store[key];
    },
    clear() {
      store = {};
    },
    key(i) {
      return Object.keys(store)[i] || null;
    },
    get length() {
      return Object.keys(store).length;
    },
  };
}

if (typeof window !== "undefined") {
  try {
    if (
      !window.localStorage ||
      typeof window.localStorage.getItem !== "function"
    ) {
      window.localStorage = createStorageMock();
    }
  } catch (err) {
    // In some environments accessing window.localStorage throws.
    window.localStorage = createStorageMock();
  }

  try {
    if (
      !window.sessionStorage ||
      typeof window.sessionStorage.getItem !== "function"
    ) {
      window.sessionStorage = createStorageMock();
    }
  } catch (err) {
    window.sessionStorage = createStorageMock();
  }
}

// Provide a minimal navigator.userAgent if tests rely on it
if (typeof navigator === "undefined")
  global.navigator = { userAgent: "node.js" };
