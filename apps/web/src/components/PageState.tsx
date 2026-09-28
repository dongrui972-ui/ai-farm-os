import type { ReactNode } from "react";

import { ErrorText, Loading } from "./Ui";

type DataPageStateProps<T> = {
  data: T | null;
  error: string;
  onRetry?: () => void;
  children: (data: T) => ReactNode;
};

export function DataPageState<T>({ data, error, onRetry, children }: DataPageStateProps<T>) {
  if (error) return <ErrorText error={error} onRetry={onRetry} />;
  if (!data) return <Loading />;
  return <>{children(data)}</>;
}
