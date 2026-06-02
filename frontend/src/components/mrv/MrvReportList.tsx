import { useState } from 'react'
import { downloadMrvPdf, downloadMrvExcel } from '../../api/dashboard'

interface Report {
  id: number
  report_month: string
  field_name: string
  total_awd_cycles: number
  flood_days: number
  status: string
}

interface MrvReportListProps {
  reports: Report[]
  onStatusChange?: () => void
}

export default function MrvReportList({ reports }: MrvReportListProps) {
  return (
    <div style={{
      background: 'white', border: '0.5px solid #e0e0e0',
      borderRadius: '12px', padding: '8px 16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0' }}>
        총 {reports.length}건
      </p>
      {reports.length === 0 ? (
        <p style={{ fontSize: '13px', color: '#aaa', padding: '24px 0', textAlign: 'center' }}>보고서가 없습니다</p>
      ) : (
        reports.map((report, i) => (
          <div key={report.id} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 0', borderBottom: i < reports.length - 1 ? '0.5px solid #f0f0f0' : 'none',
          }}>
            <div>
              <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>
                {report.field_name} · {report.report_month}
              </p>
              <p style={{ fontSize: '12px', color: '#888' }}>
                AWD {report.total_awd_cycles}회 · 담수 {report.flood_days}일
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
              <a href={downloadMrvPdf(report.id)}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '12px', padding: '5px 12px', border: '0.5px solid #ccc',
                  borderRadius: '8px', background: 'white', cursor: 'pointer',
                  textDecoration: 'none', color: '#222',
                }}
              >
                ↓ PDF
              </a>
              <a href={downloadMrvExcel(report.id)}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '12px', padding: '5px 12px', border: '0.5px solid #ccc',
                  borderRadius: '8px', background: 'white', cursor: 'pointer',
                  textDecoration: 'none', color: '#222',
                }}
              >
                ↓ Excel
              </a>
            </div>
          </div>
        ))
      )}
    </div>
  )
}


// import { downloadMrvPdf, downloadMrvExcel } from '../../api/dashboard'

// interface Report {
//   id: number
//   report_month: string
//   field_name: string
//   total_awd_cycles: number
//   flood_days: number
//   status: string
// }

// interface MrvReportListProps {
//   reports: Report[]
// }

// const statusLabel = (status: string) => {
//   if (status === 'COMPLETED') return '완료'
//   if (status === 'IN_PROGRESS') return '작성중'
//   return status
// }

// export default function MrvReportList({ reports }: MrvReportListProps) {
//   return (
//     <div style={{
//       background: 'white', border: '0.5px solid #e0e0e0',
//       borderRadius: '12px', padding: '8px 16px',
//     }}>
//       <p style={{ fontSize: '12px', color: '#888', padding: '8px 0 10px', borderBottom: '0.5px solid #f0f0f0' }}>
//         총 {reports.length}건
//       </p>
//       {reports.length === 0 ? (
//         <p style={{ fontSize: '13px', color: '#aaa', padding: '24px 0', textAlign: 'center' }}>보고서가 없습니다</p>
//       ) : (
//         reports.map((report, i) => (
//           <div key={report.id} style={{
//             display: 'flex', alignItems: 'center', justifyContent: 'space-between',
//             padding: '12px 0', borderBottom: i < reports.length - 1 ? '0.5px solid #f0f0f0' : 'none',
//           }}>
//             <div>
//               <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>
//                 {report.field_name} · {report.report_month}
//               </p>
//               <p style={{ fontSize: '12px', color: '#888' }}>
//                 AWD {report.total_awd_cycles}회 · 담수 {report.flood_days}일
//               </p>
//             </div>
//             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
//               <span style={{
//                 fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 500,
//                 background: report.status === 'COMPLETED' ? '#e8f5e9' : '#fff8e1',
//                 color: report.status === 'COMPLETED' ? '#2e7d32' : '#f57f17',
//               }}>
//                 {statusLabel(report.status)}
//               </span>
              
//               <a href={downloadMrvPdf(report.id)}
//                 target="_blank"
//                 rel="noreferrer"
//                 style={{
//                   fontSize: '12px', padding: '5px 12px', border: '0.5px solid #ccc',
//                   borderRadius: '8px', background: 'white', cursor: 'pointer',
//                   textDecoration: 'none', color: '#222',
//                 }}
//               >
//                 ↓ PDF
//               </a>
              
//               <a  href={downloadMrvExcel(report.id)}
//                 target="_blank"
//                 rel="noreferrer"
//                 style={{
//                   fontSize: '12px', padding: '5px 12px', border: '0.5px solid #ccc',
//                   borderRadius: '8px', background: 'white', cursor: 'pointer',
//                   textDecoration: 'none', color: '#222',
//                 }}
//               >
//                 ↓ Excel
//               </a>
//             </div>
//           </div>
//         ))
//       )}
//     </div>
//   )
// }