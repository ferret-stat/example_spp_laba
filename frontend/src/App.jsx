import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Files from "./pages/Files";
import MyFiles from "./pages/MyFiles";
import FileView from "./pages/FileView";
import FileEdit from "./pages/FileEdit";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

function App() {
  return (
    <>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
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
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/files/:fileId"
            element={
              <ProtectedRoute>
                <FileView />
              </ProtectedRoute>
            }
          />
          <Route
            path="/files/:fileId/edit"
            element={
              <ProtectedRoute>
                <FileEdit />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  );
}

export default App;



