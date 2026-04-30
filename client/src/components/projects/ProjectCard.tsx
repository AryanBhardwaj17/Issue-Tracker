import Link from "next/link";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import type { Project } from "@/lib/api";

interface ProjectCardProps {
  project: Project;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`} className="block">
      <Card className="cursor-pointer transition-shadow hover:shadow-md">
        <div className="mb-3 flex items-center justify-between">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg text-xs font-bold text-white"
            style={{
              background: "linear-gradient(135deg, #4f6ef7, #9b59f7)",
            }}
          >
            {project.key}
          </div>
          <Badge variant={project.role === "owner" ? "blue" : "gray"}>
            {project.role === "owner" ? "Owner" : "Member"}
          </Badge>
        </div>
        <h3 className="text-sm font-semibold text-gray-900">{project.name}</h3>
        <p className="mt-1 text-xs text-gray-500">
          {project.description || "—"}
        </p>
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          <span>{project.memberCount} {project.memberCount === 1 ? "member" : "members"}</span>
        </div>
      </Card>
    </Link>
  );
}
