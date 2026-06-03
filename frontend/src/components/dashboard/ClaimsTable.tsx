import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { useState } from "react";
import { ArrowSortUp16Regular, ArrowSortDown16Regular } from "@fluentui/react-icons";
import type { ClaimListItem } from "@/api/types";
import { palette } from "@/theme/tokens";
import { formatINR, formatDate } from "@/utils/format";
import { StatusBadge } from "@/components/common/StatusBadge";
import { FraudMeter } from "@/components/common/FraudMeter";

const TYPE_COLORS: Record<string, string> = {
  Health: palette.brand,
  Motor: "#9B6DFF",
  Property: "#22D3EE",
  Travel: palette.warning,
};

const col = createColumnHelper<ClaimListItem>();

export function ClaimsTable({ claims }: { claims: ClaimListItem[] }) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo(
    () => [
      col.accessor("claim_id", {
        header: "Claim / Claimant",
        cell: (c) => (
          <div>
            <div style={{ fontWeight: 600, fontSize: 13, color: palette.textPrimary }}>{c.getValue()}</div>
            <div style={{ fontSize: 11.5, color: palette.textMuted }}>
              {c.row.original.claimant_name} · {c.row.original.channel ?? "Web"}
            </div>
          </div>
        ),
      }),
      col.accessor("claim_type", {
        header: "Type",
        cell: (c) => {
          const t = c.getValue() ?? "—";
          const color = TYPE_COLORS[t as string] ?? palette.textMuted;
          return (
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 600,
                color,
                background: `${color}1f`,
                border: `1px solid ${color}3a`,
                padding: "2px 9px",
                borderRadius: 6,
              }}
            >
              {t}
            </span>
          );
        },
      }),
      col.accessor("claim_amount", {
        header: "Amount",
        cell: (c) => (
          <span style={{ fontSize: 13, fontWeight: 600, color: palette.textPrimary }}>
            {formatINR(c.getValue() ?? 0)}
          </span>
        ),
      }),
      col.accessor("final_payout", {
        header: "Payout",
        cell: (c) => {
          const v = c.getValue() ?? 0;
          return (
            <span style={{ fontSize: 13, fontWeight: 700, color: v > 0 ? palette.success : palette.textMuted }}>
              {formatINR(v)}
            </span>
          );
        },
      }),
      col.accessor("fraud_score", {
        header: "Fraud",
        cell: (c) => <FraudMeter score={c.getValue() ?? 0} width={84} />,
      }),
      col.accessor("decision", {
        header: "Decision",
        cell: (c) => <StatusBadge value={c.getValue() ?? c.row.original.status ?? "Processing"} size="sm" />,
      }),
      col.accessor("submitted_at", {
        header: "Date",
        cell: (c) => (
          <span style={{ fontSize: 12, color: palette.textMuted }}>{formatDate(c.getValue())}</span>
        ),
      }),
    ],
    [],
  );

  const table = useReactTable({
    data: claims,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th
                  key={h.id}
                  onClick={h.column.getToggleSortingHandler()}
                  style={{
                    textAlign: "left",
                    padding: "0 14px 10px",
                    fontSize: 10.5,
                    fontWeight: 700,
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                    color: palette.textMuted,
                    cursor: "pointer",
                    userSelect: "none",
                    whiteSpace: "nowrap",
                    borderBottom: `1px solid ${palette.glassBorder}`,
                  }}
                >
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {h.column.getIsSorted() === "asc" && <ArrowSortUp16Regular />}
                    {h.column.getIsSorted() === "desc" && <ArrowSortDown16Regular />}
                  </span>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => navigate(`/claims/${row.original.claim_id}`)}
              style={{ cursor: "pointer", transition: "background 0.12s" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  style={{
                    padding: "12px 14px",
                    borderBottom: `1px solid ${palette.glassBorder}`,
                    verticalAlign: "middle",
                  }}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
