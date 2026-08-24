export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatFileType(mime: string): string {
  const map: Record<string, string> = {
    "application/pdf": "PDF",
    "text/plain": "TXT",
    "text/markdown": "MD",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
      "DOCX",
  }
  return map[mime] ?? mime.split("/").pop()?.toUpperCase() ?? "Archivo"
}
