import { Navigate, Route, Routes } from "react-router-dom";
import Login from "../pages/Login";
import Files from "../pages/Files";
import MyFiles from "../pages/MyFiles";

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/" />;
};

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route
        path="/files"
        element={
          <ProtectedRoute>
            <Files />
          </ProtectedRoute>
        }
      />
      <Route
        path="/myfiles"
        element={
          <ProtectedRoute>
            <MyFiles />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
