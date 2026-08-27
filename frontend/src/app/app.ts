import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';

import { ListingService } from './listing.service';
import { Listing, MAX_IMAGES, ProductFolder } from './models';

@Component({
  selector: 'app-root',
  templateUrl: './app.html'
})
export class App {
  private readonly listings = inject(ListingService);

  protected readonly folders = signal<ProductFolder[]>([]);
  protected readonly selectedFolderId = signal('');
  protected readonly listing = signal<Listing | null>(null);
  protected readonly error = signal('');
  protected readonly doneMessage = signal('');
  protected readonly loadingFolders = signal(false);
  protected readonly generating = signal(false);
  protected readonly markingDone = signal(false);
  protected readonly copiedField = signal('');

  protected readonly selectedFolder = computed(
    () => this.folders().find(folder => folder.id === this.selectedFolderId()) ?? null
  );

  protected readonly tagsAsText = computed(() => this.listing()?.tags.join(', ') ?? '');

  // Said up front because each extra photo adds to what the generation costs
  protected readonly extraImagesNotice = computed(() => {
    const count = this.selectedFolder()?.images.length ?? 0;
    if (count <= 1) {
      return '';
    }
    if (count > MAX_IMAGES) {
      return `This folder has ${count} images. Only the first ${MAX_IMAGES} will be analyzed.`;
    }
    return `All ${count} images will be analyzed together for a more detailed description.`;
  });

  protected readonly extraImagesIsWarning = computed(
    () => (this.selectedFolder()?.images.length ?? 0) > MAX_IMAGES
  );

  protected readonly everythingAsText = computed(() => {
    const listing = this.listing();
    if (!listing) {
      return '';
    }
    return [
      `Title: ${listing.title}`,
      '',
      listing.description,
      '',
      `Tags: ${listing.tags.join(', ')}`,
      `Price: $${listing.price}`,
      `Size: ${listing.size}`,
      `Type: ${listing.art_type}`
    ].join('\n');
  });

  constructor() {
    this.loadFolders();
  }

  protected loadFolders(): void {
    this.loadingFolders.set(true);
    this.error.set('');

    this.listings.folders().subscribe({
      next: folders => {
        this.folders.set(folders);
        if (!folders.some(folder => folder.id === this.selectedFolderId())) {
          this.selectedFolderId.set(folders[0]?.id ?? '');
        }
        this.loadingFolders.set(false);
      },
      error: (response: HttpErrorResponse) => {
        this.error.set(this.describeError(response));
        this.loadingFolders.set(false);
      }
    });
  }

  protected selectFolder(event: Event): void {
    this.selectedFolderId.set((event.target as HTMLSelectElement).value);
    this.listing.set(null);
    this.doneMessage.set('');
  }

  protected generate(): void {
    const folderId = this.selectedFolderId();
    if (!folderId) {
      return;
    }

    this.generating.set(true);
    this.error.set('');
    this.doneMessage.set('');
    this.listing.set(null);

    this.listings.generate(folderId).subscribe({
      next: listing => {
        this.listing.set(listing);
        this.generating.set(false);
      },
      error: (response: HttpErrorResponse) => {
        this.error.set(this.describeError(response));
        this.generating.set(false);
      }
    });
  }

  protected markDone(): void {
    const listing = this.listing();
    if (!listing) {
      return;
    }

    this.markingDone.set(true);
    this.error.set('');

    this.listings.markDone(listing.folder_id).subscribe({
      next: () => {
        this.markingDone.set(false);
        this.doneMessage.set(`${listing.folder_name} moved to Processed`);
        this.listing.set(null);
        this.loadFolders();
      },
      error: (response: HttpErrorResponse) => {
        this.markingDone.set(false);
        this.error.set(this.describeError(response));
      }
    });
  }

  protected imageUrl(fileId: string, download = false): string {
    return this.listings.imageUrl(fileId, download);
  }

  protected async copy(value: string, field: string): Promise<void> {
    await navigator.clipboard.writeText(value);
    this.copiedField.set(field);

    setTimeout(() => {
      if (this.copiedField() === field) {
        this.copiedField.set('');
      }
    }, 1500);
  }

  // FastAPI puts the reason in `detail`, except for validation errors where it is a list
  private describeError(response: HttpErrorResponse): string {
    if (response.status === 0) {
      return 'Cannot reach the API. Is uvicorn running on port 8000?';
    }

    const detail = response.error?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map(item => item.msg ?? JSON.stringify(item)).join(', ');
    }

    return response.message;
  }
}
