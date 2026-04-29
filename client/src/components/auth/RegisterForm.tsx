"use client";
 
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { useAuthStore } from "@/stores/authStore";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import ErrorMessage from "@/components/ui/ErrorMessage";
 
export default function RegisterForm() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();
 
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
 
  function validate(): boolean {
    const errors: Record<string, string> = {};
 
    if (name.trim().length < 1) {
      errors.name = "Name is required";
    }

    const PASSWORD_REGEX = /^(?=.*[A-Z])(?=.*\d).{8,128}$/;


    if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    } else if (password.length > 128) {
      errors.password = "Password must be at most 128 characters";
    }

    if (!PASSWORD_REGEX.test(password)) {
      errors.password = "Password must contain at least one uppercase letter and one number";
    }
 
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }
 
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;
 
    const success = await register(name.trim(), email, password);
    if (success) {
      toast.success("Account created! Please sign in.");
      router.push("/login");
    }
  }
 
  function handleFieldChange(field: string) {
    clearError();
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }
 
  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900">
          Create an account
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Get started with your free account
        </p>
      </div>
 
      <ErrorMessage message={error} />
 
      <Input
        label="Name"
        type="text"
        placeholder="John Doe"
        value={name}
        onChange={(e) => {
          setName(e.target.value);
          handleFieldChange("name");
        }}
        error={fieldErrors.name}
        required
        autoComplete="name"
      />
 
      <Input
        label="Email"
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          handleFieldChange("email");
        }}
        error={fieldErrors.email}
        required
        autoComplete="email"
      />
 
      <Input
        label="Password"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => {
          setPassword(e.target.value);
          handleFieldChange("password");
        }}
        error={fieldErrors.password}
        required
        autoComplete="new-password"
      />
 
      <Button type="submit" isLoading={isLoading} className="w-full">
        Create account
      </Button>
 
      <p className="text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-gray-900 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}