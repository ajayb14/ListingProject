// These mirror the JSON returned by src/web/app.py, so a rename in Python breaks the build here

export interface DriveImage {
  id: string;
  name: string;
  mimeType: string;
}

export interface ProductInfo {
  painting_title: string;
  art_type: string;
  size: string;
  price: string;
}

export interface ProductFolder {
  id: string;
  name: string;
  images: DriveImage[];
  product_info: ProductInfo;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
}

export interface Listing extends ProductInfo {
  folder_id: string;
  folder_name: string;
  images: DriveImage[];
  generated_at: string;
  title: string;
  description: string;
  tags: string[];
  warnings: string[];
  model: string;
  usage?: TokenUsage;
  saved_to: string;
}

export interface MarkDoneResponse {
  folder_id: string;
  status: string;
}
