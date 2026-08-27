import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { App } from './app';

describe('App', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should ask the API for folders on startup', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    http.expectOne('/api/folders').flush([]);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Listing Generator');
  });

  it('should say every image will be analyzed when a folder holds a few', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    http.expectOne('/api/folders').flush([folderWith(['front.jpg', 'back.jpg'])]);
    await fixture.whenStable();

    const banner = (fixture.nativeElement as HTMLElement).querySelector('.banner');
    expect(banner?.textContent).toContain('All 2 images');
    expect(banner?.classList.contains('warn')).toBe(false);
  });

  it('should warn when a folder holds more images than the cap', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const names = ['a.jpg', 'b.jpg', 'c.jpg', 'd.jpg', 'e.jpg', 'f.jpg'];
    http.expectOne('/api/folders').flush([folderWith(names)]);
    await fixture.whenStable();

    const banner = (fixture.nativeElement as HTMLElement).querySelector('.banner');
    expect(banner?.textContent).toContain('Only the first 5');
    expect(banner?.classList.contains('warn')).toBe(true);
  });

  it('should stay quiet when the folder holds a single image', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    http.expectOne('/api/folders').flush([folderWith(['front.jpg'])]);
    await fixture.whenStable();

    expect((fixture.nativeElement as HTMLElement).querySelector('.banner')).toBeNull();
  });
});

function folderWith(imageNames: string[]) {
  return {
    id: 'folder-1',
    name: 'Rolling Hills_Original_8x10_100',
    images: imageNames.map(name => ({ id: `id-${name}`, name, mimeType: 'image/jpeg' })),
    product_info: {
      painting_title: 'Rolling Hills',
      art_type: 'Original',
      size: '8x10',
      price: '100'
    }
  };
}
