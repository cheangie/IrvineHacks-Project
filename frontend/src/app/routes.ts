import { createBrowserRouter } from "react-router";
import Home from "./pages/Home";
import RiskReport from "./pages/RiskReport";
import Compare from "./pages/Compare";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Home,
  },
  {
    path: "/report/:address",
    Component: RiskReport,
  },
  {
    path: "/compare/:address1/:address2",
    Component: Compare,
  },
]);