import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header banner
        self.drawString(
            54, 800, "CONFIDENTIAL // TELANGANA STATE POLICE - SPECIAL INVESTIGATION TEAM (SIT)"
        )
        self.drawRightString(540, 800, "FIR NO: 204/2026 [SPECIAL REPORT]")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 794, 540, 794)

        # Footer banner
        self.line(54, 45, 540, 45)
        self.setFont("Helvetica", 8)
        self.drawString(
            54,
            32,
            "Official Law Enforcement Investigation Docket • Handled under Strict Legal Evidentiary Custody",
        )
        self.drawRightString(540, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def create_investigation_pdf(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    title_style = ParagraphStyle(
        "DocTitle",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
    )

    sub_style = ParagraphStyle(
        "SubTitle",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#dc2626"),
        alignment=1,
    )

    sec_heading = ParagraphStyle(
        "SecHeading",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=4,
    )

    body_text = ParagraphStyle(
        "BodyDark",
        parent=normal,
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=normal,
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # Title & State Police Header
    story.append(Paragraph("TELANGANA STATE POLICE COMMISSIONERATE", title_style))
    story.append(
        Paragraph(
            "WOMEN & CHILD SAFETY WING • SPECIAL INVESTIGATION TEAM (SIT)",
            ParagraphStyle(
                "SubSub",
                parent=normal,
                fontName="Helvetica-Bold",
                fontSize=9.5,
                leading=13,
                textColor=colors.HexColor("#0284c7"),
                alignment=1,
            ),
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph("STATUTORY CRIME OCCURRENCE REPORT & CHARGE DOSSIER", sub_style)
    )
    story.append(Spacer(1, 10))

    # FIR Metadata Box
    meta_data = [
        [
            Paragraph("<b>FIR / Crime Number:</b>", body_text),
            Paragraph("<b>FIR No. 204/2026</b>", body_bold),
            Paragraph("<b>Police Station:</b>", body_text),
            Paragraph("Gachibowli Women PS, Cyberabad", body_text),
        ],
        [
            Paragraph("<b>Date & Time of FIR:</b>", body_text),
            Paragraph("28-Aug-2026 04:30 IST", body_text),
            Paragraph("<b>Case Classification:</b>", body_text),
            Paragraph(
                '<font color="#dc2626"><b>CRITICAL SPECIAL REPORT</b></font>',
                body_text,
            ),
        ],
        [
            Paragraph("<b>Legal Sections:</b>", body_text),
            Paragraph(
                "<b>Sec 376(2)(n), 354, 365, 384, 506 IPC</b><br/>r/w Sec 67A IT Act (Sec 64, 74, 137, 308 BNS)",
                body_text,
            ),
            Paragraph("<b>Lead Investigating Officer:</b>", body_text),
            Paragraph("ACP Sneha Latha, IPS<br/>(SIT Lead Investigator)", body_text),
        ],
        [
            Paragraph("<b>Date of Occurrence:</b>", body_text),
            Paragraph("26-Aug-2026 22:30 hrs to 27-Aug-2026 02:15 hrs", body_text),
            Paragraph("<b>Primary Crime Scene:</b>", body_text),
            Paragraph(
                "Safehouse Villa 18, Palm Meadows, Financial District, Hyderabad",
                body_text,
            ),
        ],
    ]

    t_meta = Table(meta_data, colWidths=[110, 150, 100, 126])
    t_meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 1. Executive Summary
    story.append(Paragraph("1. EXECUTIVE SUMMARY & MODUS OPERANDI", sec_heading))
    summary_text = (
        "On the night of 26-August-2026, the complainant (anonymized as Victim 'X', resident of Madhapur, age 24) "
        "was lured under the pretext of an executive creative project discussion at Inorbit Mall, Madhapur, and subsequently "
        "abducted in a private SUV by prime suspect <b>Vikramaditya Varma</b> and his accomplice driver <b>Kishore Yadav</b>. "
        "The victim was forcibly transported to a private safehouse located at Villa 18, Palm Meadows, Financial District, Hyderabad, "
        "where aggravated sexual assault and physical battery were committed under coercion and intimidation with a lethal weapon. "
        "Digital recordings were captured unlawfully by co-conspirator <b>Farhan Ahmed</b> for subsequent extortion demands exceeding ₹5,00,000."
    )
    story.append(Paragraph(summary_text, body_text))
    story.append(Spacer(1, 10))

    # 2. Accused & Suspect Profiles
    story.append(Paragraph("2. IDENTIFIED SUSPECTS & ACCUSED DOSSIER", sec_heading))
    suspect_data = [
        [
            Paragraph("<b>Entity / Accused</b>", body_bold),
            Paragraph("<b>Role / Tag</b>", body_bold),
            Paragraph("<b>Identifiers / Phone</b>", body_bold),
            Paragraph("<b>Address / Known Base</b>", body_bold),
        ],
        [
            Paragraph(
                "<b>Vikramaditya Varma</b><br/>(Alias: Vicky Varma, Age 32)", body_bold
            ),
            Paragraph(
                '<font color="#dc2626"><b>PRIME SUSPECT</b></font><br/>Nightclub Promoter & Financier',
                body_text,
            ),
            Paragraph(
                "Phone: <b>9848019988</b><br/>Known Associate: Kishore Yadav", body_text
            ),
            Paragraph(
                "Plot 52, Road No. 36, Jubilee Hills, Hyderabad", body_text
            ),
        ],
        [
            Paragraph("<b>Kishore Yadav</b><br/>(Alias: Kittu, Age 28)", body_bold),
            Paragraph(
                '<font color="#ea580c"><b>CO-ACCUSED / DRIVER</b></font><br/>Logistics & Transit Handler',
                body_text,
            ),
            Paragraph(
                "Phone: <b>9701122334</b><br/>Driver of TS09FA8899 SUV", body_text
            ),
            Paragraph("H.No 4-11, Site-3, Borabanda, Hyderabad", body_text),
        ],
        [
            Paragraph("<b>Farhan Ahmed</b><br/>(Alias: Danny, Age 29)", body_bold),
            Paragraph(
                '<font color="#9333ea"><b>CO-CONSPIRATOR</b></font><br/>Digital Extortion & Media Operative',
                body_text,
            ),
            Paragraph(
                "Phone: <b>9123456799</b><br/>Conduit Account: HDFC-44990012", body_text
            ),
            Paragraph(
                "Flat 302, Cyber Heights, Gachibowli, Hyderabad", body_text
            ),
        ],
        [
            Paragraph("<b>Dr. Radhika Sen</b><br/>(Medical Examiner)", body_bold),
            Paragraph(
                '<font color="#16a34a"><b>EXPERT WITNESS</b></font><br/>Forensic Medicine Specialist',
                body_text,
            ),
            Paragraph(
                "Report Ref: FSL-HYD-2026-8812<br/>Hospital: Kondapur Area Hospital",
                body_text,
            ),
            Paragraph("Government Forensic Ward, Hyderabad", body_text),
        ],
    ]
    t_suspect = Table(suspect_data, colWidths=[120, 110, 126, 130])
    t_suspect.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_suspect)
    story.append(Spacer(1, 10))

    # 3. Vehicle & Geo-Tracking
    story.append(
        Paragraph("3. VEHICLE MOVEMENTS & CRIME SCENE GEO-COORDINATES", sec_heading)
    )
    geo_data = [
        [
            Paragraph("<b>Item</b>", body_bold),
            Paragraph("<b>Details & Specifications</b>", body_bold),
            Paragraph("<b>GPS Coordinates / Address</b>", body_bold),
            Paragraph("<b>Evidentiary Confirmation</b>", body_bold),
        ],
        [
            Paragraph("<b>Transit Vehicle</b>", body_bold),
            Paragraph(
                "Mahindra Scorpio-N (Pearl White)<br/>Registration: <b>TS09FA8899</b><br/>Owner: Vikramaditya Varma",
                body_text,
            ),
            Paragraph(
                "Registered: RTA Hyderabad Central<br/>Engine No: M12-990412",
                body_text,
            ),
            Paragraph(
                "Captured on ANPR Camera at Nanakramguda Junction at 23:14 hrs on 26-Aug-2026",
                body_text,
            ),
        ],
        [
            Paragraph("<b>Primary Crime Scene</b>", body_bold),
            Paragraph("Safehouse Villa 18, Palm Meadows", body_text),
            Paragraph(
                "<b>17.4190° N, 78.3490° E</b><br/>Financial District, Nanakramguda",
                body_text,
            ),
            Paragraph(
                "Villa leased under shell entity Apex Horizon Media; DVR seized from security office",
                body_text,
            ),
        ],
        [
            Paragraph("<b>Secondary Abduction Spot</b>", body_bold),
            Paragraph("Inorbit Mall Pick-up Bay", body_text),
            Paragraph(
                "<b>17.4344° N, 78.3867° E</b><br/>Mindspace Madhapur, Hyderabad",
                body_text,
            ),
            Paragraph(
                "CCTV DVR Channel 08 logged victim forced into vehicle TS09FA8899 at 22:38 hrs",
                body_text,
            ),
        ],
    ]
    t_geo = Table(geo_data, colWidths=[100, 130, 126, 130])
    t_geo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_geo)
    story.append(Spacer(1, 10))

    # 4. CDR & Digital Forensics
    story.append(
        Paragraph("4. CALL DETAIL RECORDS (CDR) & TOWER TRIANGULATION", sec_heading)
    )
    cdr_data = [
        [
            Paragraph("<b>Caller Entity</b>", body_bold),
            Paragraph("<b>Receiver Entity</b>", body_bold),
            Paragraph("<b>Date & Time</b>", body_bold),
            Paragraph("<b>Duration</b>", body_bold),
            Paragraph("<b>Cell Tower ID / Azimuth</b>", body_bold),
        ],
        [
            Paragraph("Vikramaditya Varma<br/>(9848019988)", body_text),
            Paragraph("Kishore Yadav<br/>(9701122334)", body_text),
            Paragraph("2026-08-26 22:15:00", body_text),
            Paragraph("340 sec", body_text),
            Paragraph("HYD-TWR-MADHAPUR-08<br/>(Sector 2, 120°)", body_text),
        ],
        [
            Paragraph("Kishore Yadav<br/>(9701122334)", body_text),
            Paragraph("Farhan Ahmed<br/>(9123456799)", body_text),
            Paragraph("2026-08-26 23:45:00", body_text),
            Paragraph("195 sec", body_text),
            Paragraph("HYD-TWR-NANAKRAMGUDA-03<br/>(Sector 1, 45°)", body_text),
        ],
        [
            Paragraph("Farhan Ahmed<br/>(9123456799)", body_text),
            Paragraph("Victim Counsel<br/>(9876500112)", body_text),
            Paragraph("2026-08-27 14:20:00", body_text),
            Paragraph("180 sec", body_text),
            Paragraph("HYD-TWR-GACHIBOWLI-14<br/>(Extortion / Coercion Call)", body_text),
        ],
    ]
    t_cdr = Table(cdr_data, colWidths=[100, 100, 96, 60, 130])
    t_cdr.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_cdr)
    story.append(Spacer(1, 10))

    # 5. Financial Extortion Ledger
    story.append(Paragraph("5. EXTORTION TRANSACTIONS & MONEY TRAIL", sec_heading))
    fin_data = [
        [
            Paragraph("<b>Sender</b>", body_bold),
            Paragraph("<b>Receiver</b>", body_bold),
            Paragraph("<b>Amount (INR)</b>", body_bold),
            Paragraph("<b>Txn Reference / Mode</b>", body_bold),
            Paragraph("<b>Bank Account Conduit</b>", body_bold),
        ],
        [
            Paragraph("Vikramaditya Varma", body_text),
            Paragraph("Kishore Yadav", body_text),
            Paragraph("<b>₹1,50,000.00</b>", body_bold),
            Paragraph("TXN889920260826<br/>(IMPS Express)", body_text),
            Paragraph("HDFC Bank 0091 → ICICI Bank 998822", body_text),
        ],
        [
            Paragraph("Apex Horizon Media<br/>(Front Entity)", body_text),
            Paragraph("Farhan Ahmed", body_text),
            Paragraph("<b>₹2,20,000.00</b>", body_bold),
            Paragraph("TXN5544332211<br/>(Corporate Wire)", body_text),
            Paragraph("Axis Bank 4410 → HDFC Bank 44990012", body_text),
        ],
        [
            Paragraph("Victim Family (Demanded)", body_text),
            Paragraph("Apex Horizon Media", body_text),
            Paragraph("<b>₹5,00,000.00</b><br/>(Demand Note)", body_bold),
            Paragraph("Blackmail / Hush Escrow<br/>(Threat to Leak Media)", body_text),
            Paragraph("Flagged by Cyber Cell FIU-IND", body_text),
        ],
    ]
    t_fin = Table(fin_data, colWidths=[100, 95, 95, 96, 100])
    t_fin.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_fin)
    story.append(Spacer(1, 10))

    # 6. Seized Evidence Exhibits
    story.append(
        Paragraph("6. SEIZED FORENSIC EVIDENCE & CHAIN OF CUSTODY", sec_heading)
    )
    evi_data = [
        [
            Paragraph("<b>Exhibit ID</b>", body_bold),
            Paragraph("<b>Evidence Title & Description</b>", body_bold),
            Paragraph("<b>Custody Officer</b>", body_bold),
            Paragraph("<b>Date Seized</b>", body_bold),
            Paragraph("<b>FSL Lab Status</b>", body_bold),
        ],
        [
            Paragraph("<b>EX-01</b>", body_bold),
            Paragraph(
                "<b>DNA & Medical Swab Kit</b><br/>Collected under Sec 164A Cr.P.C. at Kondapur Area Hospital",
                body_text,
            ),
            Paragraph("SI Kavitha Reddy<br/>(Women PS)", body_text),
            Paragraph("2026-08-27", body_text),
            Paragraph(
                '<font color="#16a34a"><b>Match Confirmed</b></font><br/>FSL-HYD-2026-8812',
                body_text,
            ),
        ],
        [
            Paragraph("<b>EX-02</b>", body_bold),
            Paragraph(
                "<b>DVR Hard Disk (2TB)</b><br/>Seized from Palm Meadows Villa 18 Security Office",
                body_text,
            ),
            Paragraph("Insp. P. Naidu<br/>(Cyber Forensics)", body_text),
            Paragraph("2026-08-27", body_text),
            Paragraph("Video integrity certified under Sec 65B IEA", body_text),
        ],
        [
            Paragraph("<b>EX-03</b>", body_bold),
            Paragraph(
                "<b>2x iPhone 15 Pro Handsets</b><br/>Recovered from Vikramaditya Varma during arrest",
                body_text,
            ),
            Paragraph("ACP Sneha Latha<br/>(SIT Lead)", body_text),
            Paragraph("2026-08-28", body_text),
            Paragraph("Forensic Cellebrite extraction completed", body_text),
        ],
    ]
    t_evi = Table(evi_data, colWidths=[50, 160, 95, 75, 106])
    t_evi.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t_evi)
    story.append(Spacer(1, 15))

    # 7. Investigating Officer Sign-off Block
    sign_p = (
        "<b>INVESTIGATING OFFICER CERTIFICATION:</b><br/>"
        "I hereby certify that the contents of this Statutory Crime Report & Case Dossier have been verified through forensic DNA matching, "
        "mobile tower geolocation records, seized CCTV telemetry, and financial transaction logs. All accused persons have been booked under "
        "non-bailable provisions of Section 376(2)(n), 354, 365, 384, 506 IPC and Section 67A IT Act and produced before the Hon'ble "
        "Metropolitan Magistrate Court for judicial remand."
    )
    story.append(Paragraph(sign_p, body_text))
    story.append(Spacer(1, 15))

    sign_table_data = [
        [
            Paragraph(
                "<b>Prepared By:</b><br/>SI Kavitha Reddy<br/>Women Safety Wing, Cyberabad",
                body_text,
            ),
            Paragraph(
                "<b>Verified & Forwarded By:</b><br/>ACP Sneha Latha, IPS<br/>Chief Investigator, SIT Cyberabad",
                body_text,
            ),
            Paragraph(
                "<b>Seal of Police Station:</b><br/>[GACHIBOWLI WOMEN PS / SIT SEAL]<br/>Dated: 28-Aug-2026",
                body_text,
            ),
        ]
    ]
    t_sign = Table(sign_table_data, colWidths=[160, 160, 166])
    t_sign.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_sign)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF at: {output_path}")


if __name__ == "__main__":
    out1 = os.path.abspath("docs/sample_cases/FIR_Case_204_2026_Assault_Investigation.pdf")
    out2 = os.path.abspath("FIR_Case_204_2026_Assault_Investigation.pdf")
    create_investigation_pdf(out1)
    create_investigation_pdf(out2)
