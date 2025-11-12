import { MapPin, DollarSign, Clock, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  type: string;
  description: string;
  matchScore: number;
  applyUrl?: string;
}

interface JobCardProps {
  job: Job;
  index: number;
}

export const JobCard = ({ job, index }: JobCardProps) => {
  return (
    <div
      className="glass-card rounded-2xl p-6 hover:scale-105 transition-all duration-300 animate-glow"
      style={{
        animationDelay: `${index * 100}ms`,
      }}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-foreground mb-1">
            {job.title}
          </h3>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Building2 className="w-4 h-4" />
            <span>{job.company}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full liquid-gradient text-white text-sm font-medium">
          {job.matchScore}% Match
        </div>
      </div>

      <p className="text-muted-foreground mb-4 line-clamp-2">
        {job.description}
      </p>

      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <MapPin className="w-4 h-4" />
          <span>{job.location}</span>
        </div>
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <DollarSign className="w-4 h-4" />
          <span>{job.salary}</span>
        </div>
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <Clock className="w-4 h-4" />
          <span>{job.type}</span>
        </div>
      </div>

      <Button
        className="w-full bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-opacity rounded-full"
        onClick={() => {
          const url = job.applyUrl && /^https?:\/\//i.test(job.applyUrl)
            ? job.applyUrl
            : `https://jobs.python.org/jobs/`;
          window.open(url, "_blank");
        }}
      >
        Apply Now
      </Button>
    </div>
  );
};
