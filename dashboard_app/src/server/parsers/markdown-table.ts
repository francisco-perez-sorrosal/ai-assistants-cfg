import "server-only";

/**
 * Parses a markdown table body into an array of row objects keyed by column header.
 * - Skips the separator row (lines matching `| --- | --- |` patterns).
 * - Returns an empty array if there are fewer than 2 pipe-delimited lines.
 * - Missing cells are filled with empty strings.
 */
export function parseMarkdownTable(body: string): Array<Record<string, string>> {
  const tableLines = body
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"));

  if (tableLines.length < 2) {
    return [];
  }

  const splitRow = (row: string): string[] => row.split("|").slice(1, -1).map((cell) => cell.trim());

  const headers = splitRow(tableLines[0] ?? "");
  const dataRows = tableLines
    .slice(1)
    .filter((line) => !/^\|\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?$/.test(line));

  return dataRows.map((row) => {
    const cells = splitRow(row);
    const paddedCells =
      cells.length >= headers.length
        ? cells
        : cells.concat(Array<string>(headers.length - cells.length).fill(""));
    return headers.reduce<Record<string, string>>((record, header, index) => {
      record[header] = paddedCells[index] ?? "";
      return record;
    }, {});
  });
}
