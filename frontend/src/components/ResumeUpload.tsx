import { useState, useCallback, useRef } from "react";
import { Upload, FileText, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface ResumeUploadProps {
  onUploadComplete: (file: File) => void;
}

export const ResumeUpload = ({ onUploadComplete }: ResumeUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const { toast } = useToast();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = e.dataTransfer.files;
      if (files?.[0]) {
        handleFile(files[0]);
      }
    },
    []
  );

  const handleFile = (file: File) => {
    const validTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a PDF or Word document",
        variant: "destructive",
      });
      return;
    }

    setUploadedFile(file);
    onUploadComplete(file);
    toast({
      title: "Resume uploaded!",
      description: "Finding matching jobs for you...",
    });
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`glass-card rounded-3xl p-12 transition-all duration-300 ${
          isDragging ? "scale-105 border-primary" : ""
        } ${uploadedFile ? "border-primary/50" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          id="resume-upload"
          className="hidden"
          accept=".pdf,.doc,.docx"
          onChange={handleFileInput}
        />

        {!uploadedFile ? (
          <label
            htmlFor="resume-upload"
            className="flex flex-col items-center justify-center cursor-pointer"
          >
            <div className="mb-6 p-6 rounded-full liquid-gradient-subtle animate-float">
              <Upload className="w-12 h-12 text-primary" />
            </div>
            <h3 className="text-2xl font-semibold mb-2 text-foreground">
              Upload Your Resume
            </h3>
            <p className="text-muted-foreground mb-6 text-center">
              Drag and drop your resume here, or click to browse
            </p>
            <Button
              type="button"
              variant="default"
              size="lg"
              onClick={() => {
                const input = document.getElementById("resume-upload") as HTMLInputElement | null;
                if (input) input.click();
              }}
              className="bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-opacity rounded-full px-8"
            >
              Choose File
            </Button>
            <p className="text-sm text-muted-foreground mt-4">
              Supports PDF, DOC, DOCX
            </p>
          </label>
        ) : (
          <div className="flex flex-col items-center">
            <div className="mb-6 p-6 rounded-full bg-primary/10">
              <CheckCircle2 className="w-12 h-12 text-primary" />
            </div>
            <h3 className="text-2xl font-semibold mb-2 text-foreground">
              Resume Uploaded!
            </h3>
            <div className="flex items-center gap-2 mb-6 text-muted-foreground">
              <FileText className="w-5 h-5" />
              <span>{uploadedFile.name}</span>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setUploadedFile(null);
                const input = document.getElementById(
                  "resume-upload"
                ) as HTMLInputElement;
                if (input) input.value = "";
              }}
              className="rounded-full"
            >
              Upload Different Resume
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
