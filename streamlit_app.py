# --- USUÁRIO ---
        with col_c1:
            st.markdown("### 👤 Usuário")
            modelo.area_cliente["local"] = st.text_input("Local", value=modelo.area_cliente["local"], key="ac_local")
            modelo.area_cliente["nome_usuario"] = st.text_input("Nome do Usuário", value=modelo.area_cliente["nome_usuario"], key="ac_nome_usuario")
            
            raw_w_u = st.text_input("WhatsApp do Usuário (Apenas números)", value=modelo.area_cliente["whatsapp_usuario"], key="ac_whats_usuario")
            modelo.area_cliente["whatsapp_usuario"] = re.sub(r'\D', '', raw_w_u)
            
            st.markdown("##### Assinatura Digital em Tela (Usuário)")
            canvas_result_u = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=2,
                stroke_color="#000000",
                background_color="#ffffff",
                height=130,
                width=350,
                drawing_mode="freedraw",
                key="canvas_usuario"
            )
            # Verificação segura usando o dicionário JSON de dados de desenho (json_data)
            if canvas_result_u and canvas_result_u.json_data is not None and len(canvas_result_u.json_data.get("objects", [])) > 0:
                try:
                    if canvas_result_u.image_data is not None:
                        pil_img_u = Image.fromarray(canvas_result_u.image_data.astype('uint8'), mode="RGBA")
                        buf_u = io.BytesIO()
                        pil_img_u.save(buf_u, format="PNG")
                        modelo.area_cliente["assinatura_usuario"] = buf_u.getvalue()
                except Exception:
                    pass

        # --- COORDENADOR ---
        with col_c2:
            st.markdown("### 👔 Coordenador")
            modelo.area_cliente["data_termino"] = st.date_input("Data do término do serviço", value=modelo.area_cliente["data_termino"], key="ac_data_termino")
            modelo.area_cliente["nome_coordenador"] = st.text_input("Nome do Coordenador do setor", value=modelo.area_cliente["nome_coordenador"], key="ac_nome_coord")
            
            raw_w_c = st.text_input("WhatsApp do Coordenador (Apenas números)", value=modelo.area_cliente["whatsapp_coordenador"], key="ac_whats_coord")
            modelo.area_cliente["whatsapp_coordenador"] = re.sub(r'\D', '', raw_w_c)
            
            st.markdown("##### Assinatura Digital em Tela (Coordenador)")
            canvas_result_c = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=2,
                stroke_color="#000000",
                background_color="#ffffff",
                height=130,
                width=350,
                drawing_mode="freedraw",
                key="canvas_coordenador"
            )
            if canvas_result_c and canvas_result_c.json_data is not None and len(canvas_result_c.json_data.get("objects", [])) > 0:
                try:
                    if canvas_result_c.image_data is not None:
                        pil_img_c = Image.fromarray(canvas_result_c.image_data.astype('uint8'), mode="RGBA")
                        buf_c = io.BytesIO()
                        pil_img_c.save(buf_c, format="PNG")
                        modelo.area_cliente["assinatura_coordenador"] = buf_c.getvalue()
                except Exception:
                    pass
