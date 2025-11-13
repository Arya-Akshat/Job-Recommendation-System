import { useState, useEffect } from "react";
import { ResumeUpload } from "@/components/ResumeUpload";
import { JobCard, Job } from "@/components/JobCard";
import { Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

const mockJobs: Job[] = [
  {
    id: "1",
    title: "Senior Frontend Developer",
    company: "Tech Innovations Inc.",
    location: "San Francisco, CA",
    salary: "$120k - $180k",
    type: "Full-time",
    description:
      "We're looking for an experienced frontend developer to join our team. You'll work on cutting-edge web applications using React, TypeScript, and modern CSS frameworks.",
    matchScore: 95,
  },
  {
    id: "2",
    title: "Full Stack Engineer",
    company: "CloudScale Solutions",
    location: "Remote",
    salary: "$110k - $160k",
    type: "Full-time",
    description:
      "Join our dynamic team building scalable cloud solutions. Experience with Node.js, React, and AWS is essential.",
    matchScore: 92,
  },
  {
    id: "3",
    title: "UI/UX Developer",
    company: "Design Systems Co.",
    location: "New York, NY",
    salary: "$100k - $140k",
    type: "Full-time",
    description:
      "Create beautiful, accessible user interfaces. Strong skills in React, Tailwind CSS, and design principles required.",
    matchScore: 88,
  },
  {
    id: "4",
    title: "Software Engineer",
    company: "StartupHub",
    location: "Austin, TX",
    salary: "$90k - $130k",
    type: "Full-time",
    description:
      "Be part of our growing startup. We need versatile engineers who can work across the stack and wear multiple hats.",
    matchScore: 85,
  },
  {
    id: "5",
    title: "React Developer",
    company: "Digital Agency Pro",
    location: "Los Angeles, CA",
    salary: "$95k - $135k",
    type: "Contract",
    description:
      "Build responsive web applications for our diverse client base. Experience with modern React patterns and state management required.",
    matchScore: 82,
  },
  {
    id: "6",
    title: "Frontend Architect",
    company: "Enterprise Solutions",
    location: "Seattle, WA",
    salary: "$150k - $200k",
    type: "Full-time",
    description:
      "Lead our frontend architecture decisions and mentor junior developers. Deep expertise in React ecosystem needed.",
    matchScore: 90,
  },
];

const Index = () => {
  const [showJobs, setShowJobs] = useState(false);
  const [loading, setLoading] = useState(false);
  const [skills, setSkills] = useState<string[]>([]);
  const [experience, setExperience] = useState<number>(0);
  const [jobs, setJobs] = useState<Job[]>(mockJobs);
  const [suggestions, setSuggestions] = useState<string>("");
  const [aiLoading, setAiLoading] = useState(false);
  const [fetchingJobs, setFetchingJobs] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'ready' | 'waking'>('checking');
  const { toast } = useToast();

  // Backend API base URL - configured via VITE_API_BASE environment variable
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  
  // Debug: Log API base URL on component mount
  console.log("API_BASE configured as:", API_BASE);

  // Health check system - monitors backend readiness
  useEffect(() => {
    let checkInterval: NodeJS.Timeout;
    let attempts = 0;
    const maxAttempts = 20; // 20 attempts × 5s = 100s max wait
    
    const checkBackendHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(`${API_BASE}/`, { 
          method: "HEAD",
          signal: controller.signal 
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          console.log("✅ Backend is ready!");
          setBackendStatus('ready');
          clearInterval(checkInterval);
          
          toast({
            title: "🚀 Server Ready",
            description: "Backend is now online. You can start using the app!",
            duration: 3000
          });
        }
      } catch (err) {
        attempts++;
        console.log(`🔄 Backend check attempt ${attempts}/${maxAttempts}...`);
        
        if (attempts === 1) {
          setBackendStatus('waking');
          toast({
            title: "⏳ Starting Server",
            description: "Backend is waking up. This may take 30-60 seconds...",
            duration: 5000
          });
        }
        
        if (attempts >= maxAttempts) {
          console.error("❌ Backend failed to respond after maximum attempts");
          setBackendStatus('ready'); // Allow user to try anyway
          clearInterval(checkInterval);
          
          toast({
            title: "⚠️ Server Slow to Respond",
            description: "Backend is taking longer than expected. You can try using the app anyway.",
            variant: "destructive",
            duration: 5000
          });
        }
      }
    };
    
    // Initial check
    checkBackendHealth();
    
    // Set up interval for repeated checks
    checkInterval = setInterval(checkBackendHealth, 5000);
    
    // Cleanup on unmount
    return () => {
      if (checkInterval) clearInterval(checkInterval);
    };
  }, [API_BASE, toast]);

  const renderSuggestions = (text: string) => {
    if (!text) return null;

    // split into paragraphs by blank lines
    const sections = text.split(/\n\s*\n/).filter(Boolean);

    // Parse simple structure: detect heading-like first lines
    const parsed = sections.map((s) => ({ raw: s, lines: s.split(/\n/).map((l) => l.trim()).filter(Boolean) }));

    return (
      <div className="space-y-6">
        {parsed.map((sec, si) => {
          const lines = sec.lines;
          const first = lines[0] || '';
          const heading = /^#+\s*/.test(first) ? first.replace(/^#+\s*/, '') : null;

          // helper to shorten headings a bit for display
          const truncateHeading = (s: string, n = 48) => {
            if (!s) return s;
            if (s.length <= n) return s;
            // try to cut at last space before limit
            const cut = s.slice(0, n);
            const lastSpace = cut.lastIndexOf(' ');
            return (lastSpace > 10 ? cut.slice(0, lastSpace) : cut) + '...';
          };

          // Collect remaining text as flowing paragraphs. Remove markdown horizontal rules like '---' or '***'.
          const body = (heading ? lines.slice(1) : lines)
            .join('\n')
            .split(/\n/)
            .map((p) => p.trim())
            .filter(Boolean)
            .filter((p) => !/^[\-\*_\s]{3,}$/.test(p));

          return (
            <section
              key={si}
              className="p-6 rounded-3xl border border-white/6 bg-gradient-to-br from-white/30 to-white/5 dark:from-black/30 dark:to-black/10 backdrop-blur-md shadow-md"
            >
              {heading && (
                <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold mb-3 leading-tight text-foreground italic">
                  {renderFormatted(truncateHeading(heading, 48))}
                </h2>
              )}

              <div className="prose prose-sm sm:prose base:prose-lg text-muted-foreground">
                {body.map((para, pi) => (
                  <p key={pi} className="mb-3">{renderInlineLinks(para)}</p>
                ))}
              </div>

              {/* If any list-style lines were present originally, render as simple list (no colored circles) */}
              {sec.raw.match(/^\s*(?:[-*]|\d+[\.)])\s+/m) && (
                <ul className="mt-4 list-disc pl-6 space-y-2 text-muted-foreground">
                  {sec.raw.split(/\n/).map((l, i) => {
                    const m = /^\s*(?:[-*]|\d+[\.)])\s+(.*)/.exec(l);
                    if (!m) return null;
                    return <li key={i}>{renderInlineLinks(m[1].trim())}</li>;
                  })}
                </ul>
              )}

              {/* recommended skills chips if present (detect line key) */}
              {sec.raw.match(/recommended\s*skills?/i) && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {sec.raw
                    .split(/\n/)
                    .filter((l) => /recommended\s*skills?/i.test(l))
                    .flatMap((l) => l.split(':').slice(1).join(':').split(/,|;|\band\b/))
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .slice(0, 40)
                    .map((skill, i) => (
                      <span key={i} className="px-3 py-1 rounded-full text-sm bg-white/10 dark:bg-black/10 text-foreground border border-white/6">
                        {skill}
                      </span>
                    ))}
                </div>
              )}
            </section>
          );
        })}
      </div>
    );
  };

  // Render inline URLs as anchors with theme color
  const renderInlineLinks = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s,;]+)/;
    const parts = text.split(urlRegex).filter(Boolean);
    return (
      <>
        {parts.map((p, i) => {
          if (/^https?:\/\//.test(p)) {
            return (
              <a key={i} href={p} target="_blank" rel="noreferrer" className="text-primary underline">
                {p}
              </a>
            );
          }
          return <span key={i}>{renderFormatted(p)}</span>;
        })}
      </>
    );
  };

  // Very small inline markdown parser for **bold**, *italic*, and `code`
  const renderFormatted = (text: string) => {
    if (!text) return null;

    const nodes: Array<any> = [];
    let remaining = text;

    // Note: render both bold and italic as combined emphasis for stronger emphasis
    const tokenRe = /(\*\*([^\*]+)\*\*)|(\*([^\*]+)\*)|(`([^`]+)`)/;
    let idx = 0;
    while (remaining.length > 0) {
      const m = remaining.match(tokenRe);
      if (!m) {
        nodes.push(remaining);
        break;
      }

      const matchIdx = m.index || 0;
      if (matchIdx > 0) {
        nodes.push(remaining.slice(0, matchIdx));
      }

      if (m[1]) {
        // bold **text** (m[2]) - render with combined bold+italic for emphasis
        nodes.push(
          <strong key={`b-${idx}`} className="font-semibold">
            <em className="not-italic">{m[2]}</em>
          </strong>
        );
      } else if (m[3]) {
        // italic *text* (m[4]) - render also as bold+italic
        nodes.push(
          <strong key={`i-${idx}`} className="font-semibold italic">
            {m[4]}
          </strong>
        );
      } else if (m[5]) {
        // code `text` (m[6])
        nodes.push(
          <code key={`c-${idx}`} className="bg-muted/10 px-1 rounded text-sm font-mono">
            {m[6]}
          </code>
        );
      }

      remaining = remaining.slice((matchIdx || 0) + m[0].length);
      idx += 1;
    }

    return <>{nodes.map((n, i) => (typeof n === 'string' ? <span key={i}>{n}</span> : <span key={i}>{n}</span>))}</>;
  };

  const mapBackendToJob = (rec: any, idx: number): Job => {
    return {
      id: rec.id || String(idx),
      title: rec.Title || rec.title || "Untitled",
      company: rec["Company Name"] || rec.Company || rec.company || "",
      location: rec.Location || rec.location || "",
      salary: rec.Salary || rec.salary || "",
      type: rec["Job Type"] || rec.type || "",
      description: rec.Description || rec.description || rec["Processed Job Description"] || "",
      matchScore: Math.round((rec["Combined Score"] || rec["Match Confidence"] || 0) * 100),
      applyUrl: rec.Link || rec.link || rec.ApplyLink || rec.apply_url || rec.application_url || "",
    };
  };

  const getRecommendations = async (user_skills: string[], user_experience: number) => {
    try {
      const res = await fetch(`${API_BASE}/recommend_jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_skills, user_experience }),
      });
      if (!res.ok) throw new Error("Failed to get recommendations");
      const data = await res.json();
      const recs = data.recommendations || [];
      const mapped = recs.map((r: any, i: number) => mapBackendToJob(r, i));
      setJobs(mapped);
      setShowJobs(true);
    } catch (err: any) {
      toast({ title: "Error", description: String(err), variant: "destructive" });
    }
  };

  const handleUploadComplete = async (file: File) => {
    // Upload resume to backend
    if (!file) return;
    setLoading(true);

    // Backend currently accepts PDFs only
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast({ title: "Unsupported format", description: "Please upload a PDF for processing.", variant: "destructive" });
      setLoading(false);
      return;
    }

    try {
      console.log("Uploading file to backend", { fileName: file.name, fileType: file.type, apiUrl: `${API_BASE}/process_resume` });
      
      toast({ 
        title: "Processing resume...", 
        description: "This may take up to 60 seconds if the server is starting up.",
        duration: 3000
      });
      
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/process_resume`, {
        method: "POST",
        body: formData,
      });

      console.log("process_resume response status", res.status, res.statusText);

      const text = await res.text();
      console.log("process_resume raw response:", text);
      
      // Try parse JSON, else show raw text
      let result: any = null;
      try {
        result = JSON.parse(text);
      } catch (e) {
        console.error("process_resume returned non-JSON response", text);
      }

      if (!res.ok) {
        const errorMsg = result?.detail || text || "Failed to process resume";
        console.error("process_resume error:", errorMsg);
        throw new Error(errorMsg);
      }

      const userSkills = (result && result.skills) || [];
      const userExp = (result && result.experience) || 0;
      console.debug("Processed resume result", { userSkills, userExp, raw: result });
      setSkills(userSkills);
      setExperience(userExp);
      toast({ title: "Resume processed", description: `Found ${userSkills.length} skills` });

      // Fetch recommendations
      await getRecommendations(userSkills, userExp);
    } catch (err: any) {
      console.error("Error in handleUploadComplete", err);
      toast({ title: "Error", description: String(err), variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleAiSuggestions = async () => {
    if (!skills || skills.length === 0) {
      toast({ title: "No skills", description: "Upload a resume first to get AI suggestions.", variant: "destructive" });
      return;
    }
    setAiLoading(true);
    
    // Show helpful toast
    toast({ 
      title: "Generating AI suggestions...", 
      description: "This may take 10-20 seconds. Please wait.",
      duration: 5000
    });
    
    console.log("Requesting AI suggestions with skills:", skills);
    
    try {
      const res = await fetch(`${API_BASE}/upskill_suggestions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skills }),
      });
      
      console.log("AI suggestions response status:", res.status, res.statusText);
      
      if (!res.ok) {
        let errorMessage = "Failed to get suggestions";
        let errorTitle = "AI Suggestions Unavailable";
        
        // Try to parse error response
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          try {
            const errorData = await res.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch (parseError) {
            console.error("Failed to parse error JSON:", parseError);
          }
        } else {
          const textError = await res.text();
          if (textError) errorMessage = textError;
        }
        
        // Customize message based on status code
        if (res.status === 429 || errorMessage.toLowerCase().includes('quota')) {
          errorTitle = "⚠️ AI Quota Limit Reached";
          errorMessage = "The free Gemini API has reached its daily limit. Please try again tomorrow or upgrade to a paid plan.";
        } else if (res.status === 401 || errorMessage.toLowerCase().includes('auth')) {
          errorTitle = "🔒 Authentication Error";
          errorMessage = "API authentication failed. Please contact support.";
        } else if (res.status === 503) {
          errorTitle = "🔧 Service Unavailable";
          errorMessage = "AI service is not configured or temporarily unavailable.";
        }
        
        // Show detailed toast
        toast({ 
          title: errorTitle,
          description: errorMessage,
          variant: "destructive",
          duration: 8000
        });
        
        return; // Exit early
      }
      
      const data = await res.json();
      setSuggestions(data.suggestions || "");
      
      toast({ 
        title: "Success!", 
        description: "AI upskilling suggestions generated.",
        duration: 3000
      });
    } catch (err: any) {
      console.error("Error fetching AI suggestions:", err);
      
      // Only show generic error if we didn't already show a specific one
      if (err.name !== "AbortError") {
        toast({ 
          title: "Connection Error", 
          description: "Could not reach AI service. Please check your connection and try again.",
          variant: "destructive",
          duration: 6000
        });
      }
    } finally {
      setAiLoading(false);
    }
  };

  const handleFetchNewJobs = async () => {
    setFetchingJobs(true);
    try {
      const res = await fetch(`${API_BASE}/fetch_new_jobs`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to fetch new jobs");
      const data = await res.json();
      toast({ title: "Jobs updated", description: data.message || "Jobs refreshed" });
      // Refresh recommendations if we already have skills
      if (skills && skills.length > 0) await getRecommendations(skills, experience);
    } catch (err: any) {
      toast({ title: "Error", description: String(err), variant: "destructive" });
    } finally {
      setFetchingJobs(false);
    }
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16 animate-float">
          <div className="inline-flex items-center justify-center gap-3 mb-6">
            <div className="p-3 rounded-2xl liquid-gradient">
              <Briefcase className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold mb-4 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
            Find Your Perfect Job
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload your resume and discover opportunities tailored to your skills
          </p>
        </div>

        {/* Upload Section */}
        {!showJobs && (
          <div className="mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <ResumeUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <Button
            onClick={handleAiSuggestions}
            disabled={aiLoading}
            className="bg-gradient-to-r from-primary to-secondary rounded-full px-6"
          >
            {aiLoading ? "Generating..." : "AI Upskill Suggestions"}
          </Button>
          <Button
            onClick={handleFetchNewJobs}
            disabled={fetchingJobs}
            variant="outline"
            className="rounded-full px-6"
          >
            {fetchingJobs ? "Fetching..." : "Fetch New Jobs"}
          </Button>
        </div>

        {/* AI Suggestions Display */}
        {suggestions && (
          <div className="glass-card rounded-2xl p-6 mb-8">
            <h3 className="text-lg font-semibold mb-2">AI Upskill Suggestions</h3>
            <div className="text-muted-foreground">
              {renderSuggestions(suggestions)}
            </div>
          </div>
        )}

        {/* Jobs Section */}
        {showJobs && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-2 text-foreground">
                Top Matches for You
              </h2>
              <p className="text-muted-foreground">{jobs.length} opportunities found based on your resume</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job, index) => (
                <JobCard key={job.id} job={job} index={index} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
