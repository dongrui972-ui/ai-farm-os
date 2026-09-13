import type { ReactNode } from "react";

import { ErrorText, Loading } from "./Ui";

type DataPageStateProps<T> = {
  data: T | null;
  error: string;
  children: (data: T) => ReactNode;
};

export function DataPageState<T>({ data, error, children }: DataPageStateProps<T>) {
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return <>{children(data)}</>;
}
