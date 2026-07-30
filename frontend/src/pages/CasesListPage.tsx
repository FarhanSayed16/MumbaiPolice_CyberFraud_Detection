import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { caseService, type CaseItem } from "@/api/client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { PlusCircle, Search, RefreshCw, AlertCircle, ShieldAlert, ChevronLeft, ChevronRight } from "lucide-react";
import { CaseIntakeModal } from "@/components/cases/CaseIntakeModal";

const PAGE_SIZE = 10;

export const CasesListPage: React.FC = () => {
  const { t } = useTranslation();
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [sortBy, setSortBy] = useState<"created_at" | "risk" | "amount">("created_at");
  const [page, setPage] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [isIntakeOpen, setIsIntakeOpen] = useState<boolean>(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await caseService.listCases({
        search: search.trim() || undefined,
        page,
        size: PAGE_SIZE,
        sort_by: sortBy,
      });
      setCases(data.items || []);
      setTotal(data.total ?? 0);
    } catch {
      setError(t("case.fetchError"));
      setCases([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [search, page, sortBy]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200 tracking-tight flex items-center gap-2">
            <span>{t("case.title")}</span>
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">{t("case.subtitle")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadCases} className="gap-2 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span>{t("case.refresh")}</span>
          </Button>
          <Button size="sm" onClick={() => setIsIntakeOpen(true)} className="gap-2 font-bold shadow-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary">
            <PlusCircle className="h-4 w-4" />
            <span>{t("case.newIntake")}</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded-lg flex items-center gap-3 text-red-800 dark:text-red-200 text-sm">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex items-center gap-4 bg-white dark:bg-slate-900 p-4 rounded-lg border shadow-sm focus-within:ring-2 focus-within:ring-primary focus-within:border-transparent">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" aria-hidden="true" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={t("case.searchPlaceholder")}
            aria-label={t("case.searchLabel")}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-700 rounded-md text-sm bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => {
            setSortBy(e.target.value as "created_at" | "risk" | "amount");
            setPage(1);
          }}
          aria-label="Sort cases"
          className="py-2 px-3 border border-slate-200 dark:border-slate-700 rounded-md text-sm bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 min-w-[140px]"
        >
          <option value="created_at">{t("casesList.newestFirst")}</option>
          <option value="risk">Highest risk</option>
          <option value="amount">Amount at risk</option>
        </select>
      </div>

      <Card>
        <CardHeader className="pb-3 border-b flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold">{t("case.queueTitle")}</CardTitle>
            <CardDescription>
              {loading
                ? t("case.queueDescriptionLoading")
                : t("case.queueDescription", { count: cases.length })}
            </CardDescription>
          </div>
          <Badge variant="outline" className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            {t("case.phaseActive")}
          </Badge>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y">
            {loading ? (
              <div className="p-4 space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-sm">
                {t("case.noResults")}
              </div>
            ) : (
              cases.map((c) => (
                <div key={c.id} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5">
                      <Link
                        to={`/cases/${c.id}`}
                        className="font-bold text-primary hover:underline text-base font-mono focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary rounded-sm"
                      >
                        {c.case_number}
                      </Link>
                      <Badge variant="secondary" className="uppercase text-[11px] font-semibold">
                        {c.fraud_category?.replace("_", " ")}
                      </Badge>
                      {c.duplicate_of_case_id && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700">
                          <ShieldAlert className="h-3 w-3" />
                          {t("case.duplicateLinked")}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span>{t("case.reported")}: {new Date(c.reported_at || c.created_at).toLocaleDateString("en-IN")}</span>
                      {c.ncrp_acknowledgement_number && (
                        <span className="font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded">
                          NCRP: {c.ncrp_acknowledgement_number}
                        </span>
                      )}
                      {c.fir_number && (
                        <span className="font-mono bg-blue-50 dark:bg-blue-900/40 text-blue-800 px-1.5 py-0.5 rounded border border-blue-200 dark:border-blue-700">
                          FIR: {c.fir_number}
                        </span>
                      )}
                      <span>{t("case.triageStatus")}: <strong className="text-slate-700 dark:text-slate-300 uppercase">{c.status}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">{t("case.amountAtRisk")}</p>
                      <p className="font-bold text-slate-800 dark:text-slate-200 text-base">{formatCurrency(c.amount_at_risk || 0)}</p>
                    </div>
                    <Link to={`/cases/${c.id}`} tabIndex={-1}>
                      <Button variant="outline" size="sm" className="font-semibold shadow-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary">
                        {t("case.openCockpit")}
                      </Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>

          {!loading && total > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t("case.pagination.pageInfo", { page, totalPages, total })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  aria-label={t("case.pagination.prev")}
                  className="gap-1"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Prev
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  aria-label={t("case.pagination.next")}
                  className="gap-1"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <CaseIntakeModal
        isOpen={isIntakeOpen}
        onClose={() => setIsIntakeOpen(false)}
        onSuccess={() => loadCases()}
      />
    </div>
  );
};
