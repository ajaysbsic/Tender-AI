import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environments/environment';

export interface TenderEvaluation {
  tender_id: string;
  overall_score: number;
  bid_recommendation: string;
  scores: {
    eligibility: { score: number; category: string };
    risk: { score: number; category: string };
    effort: { score: number; category: string };
  };
  strengths: string[];
  weaknesses: string[];
  critical_items: string[];
}

export interface EligibilityDetails {
  category: string;
  score_percentage: number;
  requirements_met: number;
  total_requirements: number;
  requirements: Array<{
    text: string;
    met: boolean;
    mandatory: boolean;
    reasoning: string;
  }>;
}

export interface UploadResponse {
  tender_id: string;
  filename: string;
  status: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Tender endpoints
  uploadTender(file: File, companyDescription?: string): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (companyDescription) {
      formData.append('company_description', companyDescription);
    }
    return this.http.post<UploadResponse>(`${this.apiUrl}/tender/upload`, formData);
  }

  getTenderStatus(tenderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/tender/${tenderId}/status`);
  }

  // Evaluation endpoints
  getEvaluation(tenderId: string): Observable<TenderEvaluation> {
    return this.http.get<TenderEvaluation>(`${this.apiUrl}/evaluations/tender/${tenderId}`);
  }

  getEligibilityDetails(tenderId: string): Observable<EligibilityDetails> {
    return this.http.get<EligibilityDetails>(
      `${this.apiUrl}/evaluations/tender/${tenderId}/eligibility`
    );
  }

  getRiskAssessment(tenderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/evaluations/tender/${tenderId}/risk`);
  }

  getEffortAssessment(tenderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/evaluations/tender/${tenderId}/effort`);
  }

  downloadPdfReport(tenderId: string, companyName: string): Observable<Blob> {
    const params = new HttpParams().set('company_name', companyName);
    return this.http.get(
      `${this.apiUrl}/evaluations/tender/${tenderId}/report/pdf`,
      { params, responseType: 'blob' }
    );
  }

  getReportSummary(tenderId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/evaluations/tender/${tenderId}/report/summary`);
  }

  listEvaluations(status?: string, limit: number = 50, offset: number = 0): Observable<any> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    if (status) {
      params = params.set('status', status);
    }

    return this.http.get(`${this.apiUrl}/evaluations/list`, { params });
  }

  // Company profile endpoints
  getCompanyProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/company/profile`);
  }

  updateCompanyProfile(profile: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/company/profile`, profile);
  }
}
