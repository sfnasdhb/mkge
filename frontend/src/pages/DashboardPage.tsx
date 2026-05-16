import { useAuthStore } from "@/features/auth/store";
import { useLogout } from "@/features/auth/hooks";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-bold text-lg text-gray-900">MKGE</span>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
            {user?.role}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user?.full_name}</span>
          <button
            onClick={logout}
            className="text-sm text-red-600 hover:underline font-medium"
          >
            Đăng xuất
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Chào mừng, {user?.full_name}!
          </h2>
          <p className="text-gray-500 mb-10">
            Phase 0 hoàn thành — Upload + Pipeline sẽ có trong Phase 1 & 2.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
            {[
              { label: "Documents", desc: "Upload PDF y khoa", phase: "Phase 1" },
              { label: "Graph", desc: "Khám phá Knowledge Graph", phase: "Phase 2" },
              { label: "Query", desc: "Hỏi đáp GraphRAG", phase: "Phase 3" },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-white rounded-xl border border-gray-200 p-6 text-left opacity-60 cursor-not-allowed"
              >
                <p className="font-semibold text-gray-900">{item.label}</p>
                <p className="text-sm text-gray-500 mt-1">{item.desc}</p>
                <span className="inline-block mt-3 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                  {item.phase}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
