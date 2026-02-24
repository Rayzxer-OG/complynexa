import { UploadForm } from "@/components/UploadForm";

export default function UploadPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-slate-900">Compliance upload</h1>
        <p className="text-sm text-slate-600">
          Upload a multi-document PDF. We&apos;ll split by &quot;REPORT No.&quot;, extract expiry dates, and create document entries. When done, you&apos;ll be redirected to the dashboard.
        </p>
        <div className="max-w-md">
          <UploadForm />
        </div>
      </div>
    </div>
  );
}
