import { useState } from "react";
import { motion } from "framer-motion";
import { Building2, CalendarDays, Download, ExternalLink, FileText, Landmark, Leaf } from "lucide-react";
import {
  getAnnouncements,
  getAnnualReports,
  getBoardMeetings,
  getBrsr,
  getCorporateActions,
  getEvents,
  getQuarterlyResults,
} from "@/api/services";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCorporateData } from "@/hooks/queries";
import { formatLakhs, formatMaybe } from "@/lib/format";
import { cn } from "@/lib/utils";

function PanelSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}

function PanelError() {
  return (
    <p className="py-8 text-center text-sm text-muted-foreground">
      NSE live data unavailable right now — try again shortly.
    </p>
  );
}

function ExternalDoc({ url, label = "PDF" }: { url: string | null; label?: string }) {
  if (!url) return null;
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="inline-flex shrink-0 items-center gap-1 rounded-md bg-secondary/70 px-2 py-1 text-[11px] font-medium text-primary transition-colors hover:bg-secondary"
    >
      <Download className="h-3 w-3" /> {label}
    </a>
  );
}

export function CorporatePanel({ symbol }: { symbol: string }) {
  const [tab, setTab] = useState("announcements");

  const announcements = useCorporateData("announcements", symbol, getAnnouncements, tab === "announcements");
  const actions = useCorporateData("actions", symbol, getCorporateActions, tab === "actions");
  const events = useCorporateData("events", symbol, getEvents, tab === "events");
  const meetings = useCorporateData("meetings", symbol, getBoardMeetings, tab === "meetings");
  const results = useCorporateData("results", symbol, getQuarterlyResults, tab === "results");
  const reports = useCorporateData("reports", symbol, getAnnualReports, tab === "reports");
  const brsr = useCorporateData("brsr", symbol, getBrsr, tab === "brsr");

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
      <Card className="glass-hover">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Landmark className="h-4 w-4 text-primary" /> Corporate Intelligence
          </CardTitle>
          <Badge variant="muted" className="normal-case tracking-normal">
            live · NSE filings
          </Badge>
        </CardHeader>
        <CardContent>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="h-auto flex-wrap">
              <TabsTrigger value="announcements">Announcements</TabsTrigger>
              <TabsTrigger value="actions">Corp Actions</TabsTrigger>
              <TabsTrigger value="events">Events</TabsTrigger>
              <TabsTrigger value="meetings">Board Meetings</TabsTrigger>
              <TabsTrigger value="results">Results</TabsTrigger>
              <TabsTrigger value="reports">Annual Reports</TabsTrigger>
              <TabsTrigger value="brsr">BRSR</TabsTrigger>
            </TabsList>

            {/* Announcements */}
            <TabsContent value="announcements">
              {announcements.isLoading ? (
                <PanelSkeleton />
              ) : announcements.isError ? (
                <PanelError />
              ) : (
                <div className="space-y-1">
                  {announcements.data?.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg px-2 py-2.5 hover:bg-accent/40">
                      <FileText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{a.subject}</p>
                        {a.details && (
                          <p className="mt-0.5 line-clamp-2 text-xs leading-snug text-muted-foreground">{a.details}</p>
                        )}
                        <p className="mt-1 text-[11px] text-muted-foreground/70">{a.broadcastAt}</p>
                      </div>
                      <ExternalDoc url={a.attachmentUrl} />
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Corporate actions */}
            <TabsContent value="actions">
              {actions.isLoading ? (
                <PanelSkeleton />
              ) : actions.isError ? (
                <PanelError />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Action</TableHead>
                      <TableHead className="text-right">Ex-Date</TableHead>
                      <TableHead className="text-right">Record Date</TableHead>
                      <TableHead className="text-right">Face Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {actions.data?.map((a, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-sm">{a.subject}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">{a.exDate ?? "—"}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">{a.recordDate ?? "—"}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">₹{a.faceValue ?? "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>

            {/* Events + board meetings share a layout */}
            {(["events", "meetings"] as const).map((key) => {
              const q = key === "events" ? events : meetings;
              return (
                <TabsContent key={key} value={key}>
                  {q.isLoading ? (
                    <PanelSkeleton />
                  ) : q.isError ? (
                    <PanelError />
                  ) : (
                    <div className="space-y-1">
                      {q.data?.map((e, i) => (
                        <div key={i} className="flex items-start gap-3 rounded-lg px-2 py-2.5 hover:bg-accent/40">
                          <CalendarDays className="mt-0.5 h-4 w-4 shrink-0 text-chart-4" />
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-mono text-xs font-semibold text-foreground">{e.date}</span>
                              {e.purpose && (
                                <Badge variant="muted" className="normal-case tracking-normal">
                                  {e.purpose}
                                </Badge>
                              )}
                            </div>
                            {e.description && (
                              <p className="mt-1 line-clamp-3 text-xs leading-snug text-muted-foreground">
                                {e.description}
                              </p>
                            )}
                          </div>
                          <ExternalDoc url={e.attachmentUrl} label="Filing" />
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              );
            })}

            {/* Reported results */}
            <TabsContent value="results">
              {results.isLoading ? (
                <PanelSkeleton />
              ) : results.isError ? (
                <PanelError />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Period</TableHead>
                      <TableHead className="text-right">Total Income</TableHead>
                      <TableHead className="text-right">PBT</TableHead>
                      <TableHead className="text-right">Net Profit</TableHead>
                      <TableHead className="text-right">EPS</TableHead>
                      <TableHead className="text-right">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.data?.map((r, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono text-xs font-semibold">{r.period}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">{formatLakhs(r.totalIncome)}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">{formatLakhs(r.profitBeforeTax)}</TableCell>
                        <TableCell
                          className={cn(
                            "text-right font-mono text-xs tabular",
                            r.netProfit !== null && (r.netProfit >= 0 ? "text-bull" : "text-bear"),
                          )}
                        >
                          {formatLakhs(r.netProfit)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs tabular">{formatMaybe(r.eps)}</TableCell>
                        <TableCell className="text-right text-[11px] text-muted-foreground">{r.audited}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>

            {/* Annual reports */}
            <TabsContent value="reports">
              {reports.isLoading ? (
                <PanelSkeleton />
              ) : reports.isError ? (
                <PanelError />
              ) : (
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {reports.data?.map((r, i) => (
                    <a
                      key={i}
                      href={r.fileUrl ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="group flex items-center gap-3 rounded-xl border border-border/60 bg-secondary/30 p-3 transition-colors hover:border-primary/40"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Building2 className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold">
                          FY {r.fromYear}–{r.toYear?.slice(-2)}
                        </p>
                        <p className="text-[11px] text-muted-foreground">{r.fileSize ?? "PDF"}</p>
                      </div>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
                    </a>
                  ))}
                </div>
              )}
            </TabsContent>
            {/* BRSR — sustainability reports */}
            <TabsContent value="brsr">
              {brsr.isLoading ? (
                <PanelSkeleton />
              ) : brsr.isError ? (
                <PanelError />
              ) : brsr.data?.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">No BRSR filings yet.</p>
              ) : (
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {brsr.data?.map((r, i) => (
                    <a
                      key={i}
                      href={r.attachmentUrl ?? "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="group flex items-center gap-3 rounded-xl border border-border/60 bg-secondary/30 p-3 transition-colors hover:border-primary/40"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-bull/10 text-bull">
                        <Leaf className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold">
                          BRSR FY {r.fyFrom}–{r.fyTo?.slice(-2)}
                        </p>
                        <p className="text-[11px] text-muted-foreground">{r.fileSize ?? "PDF"}</p>
                      </div>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
                    </a>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  );
}
