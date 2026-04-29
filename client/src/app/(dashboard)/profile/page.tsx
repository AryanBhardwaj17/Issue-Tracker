"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { changePassword } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errors";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import ErrorMessage from "@/components/ui/ErrorMessage";

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(res.message);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      // Server revokes all sessions — log out the client too
      await logout();
      router.replace("/login");
    } catch (err: unknown) {
      setError(extractErrorMessage(err, "Failed to change password."));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 p-6">
      {/* Profile info */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Profile</h2>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="font-medium text-gray-500">Name</dt>
            <dd className="text-gray-900">{user?.name}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="font-medium text-gray-500">Email</dt>
            <dd className="text-gray-900">{user?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="font-medium text-gray-500">Member since</dt>
            <dd className="text-gray-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : "—"}
            </dd>
          </div>
        </dl>
      </Card>

      {/* Change password */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Change Password
        </h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Current password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
          <Input
            label="New password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
          <Input
            label="Confirm new password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
          <ErrorMessage message={error} />
          {success && (
            <p className="text-sm text-green-600">{success}</p>
          )}
          <Button type="submit" isLoading={isLoading} className="w-full">
            Update password
          </Button>
        </form>
      </Card>

      {/* Logout */}
      <Card>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">Session</h2>
        <Button variant="danger" onClick={handleLogout} className="w-full">
          Logout
        </Button>
      </Card>
    </div>
  );
}
