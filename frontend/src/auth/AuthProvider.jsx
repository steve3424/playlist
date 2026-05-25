import { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  console.log("AuthProvider called")

  useEffect(() => {
    async function checkAuth() {
      console.log("checkAuth called")
      try {

        const response = await fetch("http://localhost/api/v1/users/whoami", {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data.name);
        } else {
          setUser(null);
        }
      } catch (err) {
        setUser(null);
      } finally {
        console.log("checkAuth finished")
        setIsLoading(false);
      }
    }

    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        authenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}