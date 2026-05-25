import React from "react";
import { Users, FileText, MessageSquare, Database, Share2 } from "lucide-react";
import { Card, CardContent } from "@/shared/components/ui/card";
import type { AdminStats } from "../api";

interface StatsCardsProps {
  stats?: AdminStats;
  isLoading: boolean;
}

export const StatsCards: React.FC<StatsCardsProps> = ({ stats, isLoading }) => {
  const cards = [
    {
      title: "Tổng Người Dùng",
      value: stats?.total_users ?? 0,
      icon: Users,
      gradient: "from-blue-500/10 to-indigo-500/10 border-blue-500/20 text-blue-500",
      bgIcon: "bg-blue-500/15",
    },
    {
      title: "Tài Liệu Đã Tải",
      value: stats?.total_documents ?? 0,
      icon: FileText,
      gradient: "from-emerald-500/10 to-teal-500/10 border-emerald-500/20 text-emerald-500",
      bgIcon: "bg-emerald-500/15",
    },
    {
      title: "Tổng Số Câu Hỏi (Queries)",
      value: stats?.total_queries ?? 0,
      icon: MessageSquare,
      gradient: "from-purple-500/10 to-pink-500/10 border-purple-500/20 text-purple-500",
      bgIcon: "bg-purple-500/15",
    },
    {
      title: "Thực Thể (Entities)",
      value: stats?.total_entities ?? 0,
      icon: Database,
      gradient: "from-amber-500/10 to-orange-500/10 border-amber-500/20 text-amber-500",
      bgIcon: "bg-amber-500/15",
    },
    {
      title: "Quan Hệ (Relationships)",
      value: stats?.total_relationships ?? 0,
      icon: Share2,
      gradient: "from-rose-500/10 to-red-500/10 border-rose-500/20 text-rose-500",
      bgIcon: "bg-rose-500/15",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card
            key={idx}
            className={`relative overflow-hidden bg-gradient-to-br ${card.gradient} transition-all duration-300 hover:shadow-md hover:scale-[1.01]`}
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {card.title}
                </span>
                <div className={`rounded-lg p-2 ${card.bgIcon}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-4 flex items-baseline">
                {isLoading ? (
                  <div className="h-9 w-20 animate-pulse rounded bg-muted/50" />
                ) : (
                  <span className="text-3xl font-extrabold tracking-tight">
                    {card.value.toLocaleString()}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
