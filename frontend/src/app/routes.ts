import { createBrowserRouter } from "react-router";
import Home from "./pages/Home";
import RiskReport from "./pages/RiskReport";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Home,
  },
  {
    path: "/report/:address",
    Component: RiskReport,
  },
]);
