import { Skeleton } from '@/components/ui/skeleton';

interface Props {
  rows?: number;
  cols: number;
}

export function LoadingRows({ rows = 6, cols }: Props) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r} aria-hidden="true">
          {Array.from({ length: cols }).map((__, c) => (
            <td key={c} className="px-3 py-2">
              <Skeleton className="h-4 w-full" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}