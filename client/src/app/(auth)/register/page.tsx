import RegisterForm from "@/components/auth/RegisterForm";
import Card from "@/components/ui/Card";
 
export default function RegisterPage() {
  return (
    <Card className="w-full max-w-md">
      <RegisterForm />
    </Card>
  );
}