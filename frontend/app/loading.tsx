import { ShieldAlert } from "lucide-react";

export default function Loading() {
  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center">
      <ShieldAlert className="h-12 w-12 text-blue-400 animate-pulse mb-4" />
      <h1 className="text-xl font-bold text-white mb-2">
        Karachi Flood Early Warning System
      </h1>
      <p className="text-sm text-slate-500">
        Connecting to weather station...
      </p>
    </main>
  );
}
