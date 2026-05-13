import type { Metadata } from "next";
import { MedicalChat } from "../components/MedicalChat";

export const metadata: Metadata = {
  title: "Medical Evidence Assistant",
  description: "Retrieval-grounded clinical evidence UI",
};

export default function Home() {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return <MedicalChat apiBase={api} />;
}
