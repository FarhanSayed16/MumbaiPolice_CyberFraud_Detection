import React, { useState, useEffect, useRef } from "react";
import { Search, Loader2, FileText, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { caseService } from "@/api/client";
import { CaseListResponse } from "@/api/client"; // Will need to define/import it if not present, wait it's in client.ts... wait let me check
// Actually I can just type it as any for now or let TS infer it if imported correctly. Let's import CaseItem.
import { CaseItem } from "@/api/client";

export const GlobalSearch: React.FC = () => {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<CaseItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Debounce search
  useEffect(() => {
    if (query.trim().length < 3) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    
    const timeout = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await caseService.searchCases(query);
        setResults(data.items || []);
        setIsOpen(true);
      } catch (err) {
        console.error("Search failed", err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);
    
    return () => clearTimeout(timeout);
  }, [query]);

  // Click outside to close
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSelect = (caseId: string) => {
    setIsOpen(false);
    setQuery("");
    navigate(`/cases/${caseId}`);
  };

  return (
    <div className="relative w-80" ref={containerRef}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-slate-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-9 pr-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-md leading-5 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:bg-white dark:focus:bg-slate-700 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
          placeholder="Search cases, accounts, phones..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (query.trim().length >= 3) setIsOpen(true) }}
        />
        {loading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
          </div>
        )}
      </div>

      {isOpen && (
        <div className="absolute mt-1 w-full bg-white dark:bg-slate-900 shadow-lg dark:shadow-slate-900/50 rounded-md border border-slate-200 dark:border-slate-700 z-50 max-h-96 overflow-y-auto">
          {results.length === 0 && !loading ? (
            <div className="p-4 text-sm text-slate-500 dark:text-slate-400 flex flex-col items-center">
              <AlertCircle className="h-5 w-5 mb-1 text-slate-400" />
              No cases found
            </div>
          ) : (
            <ul className="py-1">
              {results.map((c) => (
                <li
                  key={c.id}
                  className="px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer border-b border-slate-100 dark:border-slate-800 last:border-0"
                  onClick={() => handleSelect(c.id)}
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{c.case_number}</span>
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex justify-between">
                    <span className="uppercase">{c.fraud_category}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold
                      ${c.status === 'closed' ? 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400' : 'bg-green-100 dark:bg-emerald-900/40 text-green-700 dark:text-emerald-400'}
                    `}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
