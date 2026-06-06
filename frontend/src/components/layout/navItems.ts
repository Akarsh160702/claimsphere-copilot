import {
  Board20Regular,
  DocumentAdd20Regular,
  AppsList20Regular,
  DataTrending20Regular,
  Search20Regular,
  PeopleTeam20Regular,
  type FluentIcon,
} from "@fluentui/react-icons";

export interface NavItem {
  path: string;
  label: string;
  icon: FluentIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { path: "/dashboard", label: "Dashboard", icon: Board20Regular },
  { path: "/intake", label: "New Claim", icon: DocumentAdd20Regular },
  { path: "/claims", label: "Claims", icon: AppsList20Regular },
  { path: "/monitor", label: "Agent Monitor", icon: DataTrending20Regular },
  { path: "/search", label: "Policy Search", icon: Search20Regular },
  { path: "/review", label: "Review Queue", icon: PeopleTeam20Regular },
];
