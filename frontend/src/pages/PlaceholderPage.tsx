import { Construction } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { EmptyState } from "@/shared/components/EmptyState";
import { PageHeader } from "@/shared/components/PageHeader";

interface Props {
  title: string;
  description: string;
  phase: string;
}

export default function PlaceholderPage({ title, description, phase }: Props) {
  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={description}
        actions={<Badge variant="outline">{phase}</Badge>}
      />
      <EmptyState
        icon={<Construction className="h-6 w-6" />}
        title="Tính năng đang phát triển"
        description={`${title} sẽ được hoàn thiện trong ${phase}. Hiện đang sử dụng UI shell và mock data.`}
      />
    </div>
  );
}
