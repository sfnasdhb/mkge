import RegisterForm from "@/features/auth/components/RegisterForm";

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Tạo tài khoản</h1>
            <p className="text-sm text-gray-500 mt-1">Medical Knowledge Graph Extraction</p>
          </div>
          <RegisterForm />
        </div>
      </div>
    </div>
  );
}
