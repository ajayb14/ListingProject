import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Listing, MarkDoneResponse, ProductFolder } from './models';

@Injectable({ providedIn: 'root' })
export class ListingService {
  private readonly http = inject(HttpClient);

  folders(): Observable<ProductFolder[]> {
    return this.http.get<ProductFolder[]>('/api/folders');
  }

  generate(folderId: string): Observable<Listing> {
    return this.http.post<Listing>('/api/generate', { folder_id: folderId });
  }

  markDone(folderId: string): Observable<MarkDoneResponse> {
    return this.http.post<MarkDoneResponse>('/api/mark-done', { folder_id: folderId });
  }

  // The browser hits this directly, so it returns a URL rather than bytes
  imageUrl(fileId: string, download = false): string {
    return `/api/image/${fileId}${download ? '?download=1' : ''}`;
  }
}
