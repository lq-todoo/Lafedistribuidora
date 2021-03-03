# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from lxml import etree
from odoo.tools.safe_eval import test_python_expr
import xml.etree.ElementTree as ET
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    allow_in_product_view = fields.Boolean('Allwed this Pricelist in Product Tree view?')

    def delete_common_dynamic(self):
        count = 1
        # for pricelist_id in self.search([('allow_in_product_view', '=', True)]):
        for pricelist_id in self.search([]):
            field_name = 'x_pricelist_' + str(count)
            label_name = 'Pricelist ' + str(count)
            view_id = self.env['ir.ui.view'].search([('model', '=', 'product.product'), ('type', '=', 'tree'), ('name', '=', str(pricelist_id.id))])
            if view_id:
                view_id.unlink()
            count += 1

        count = 1
        # for pricelist_id in self.search([('allow_in_product_view', '=', True)]):
        for pricelist_id in self.search([]):
            field_name = 'x_pricelist_' + str(count)
            field_id = self.env['ir.model.fields'].search([('model_id.model', '=', 'product.product'), ('name', '=', field_name)])
            if field_id:
                field_id.unlink()
            count += 1

    def create_common_dynamic(self):
        count = 1
        for pricelist_id in self.search([('allow_in_product_view', '=', True)]):
            field_name = 'x_pricelist_' + str(count)
            label_name = 'Pricelist ' + str(count)
            pricelist_id.action_add(field_name, label_name)
            count += 1

    @api.model
    def create(self, vals):
        res = super(ProductPricelist, self).create(vals)
        res.delete_common_dynamic()
        res.create_common_dynamic()
        return res

    def write(self, vals):
        res = super(ProductPricelist, self).write(vals)
        self.delete_common_dynamic()
        self.create_common_dynamic()
        return res

    # def unlink(self):
    #     res = super(ProductPricelist, self).unlink()
    #     for rec in self:
    #         rec.delete_common_dynamic()
    #         rec.create_common_dynamic()
    #     return res

    def add_new_dynamic_fields(self, field_name, label_name):
        model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
        ir_model_fields_obj = self.env['ir.model.fields']
        values = {
            'model_id': model_id.id,
            'ttype': 'char',
            'name': field_name,
            'field_description': label_name,
            'model': 'product.product',
            'column1': str(self.id),
        }
        try:
            ir_model_fields_obj.create(values)
        except Exception as e:
            raise ValidationError(e)

    def xml_field_arch(self, field_name, label_name):
        xpath = etree.Element('xpath')
        name = 'product_template_attribute_value_ids'
        expr = '//' + 'field' + '[@name="' + name + '"]'
        xpath.set('expr', expr)
        xpath.set('position', 'before')
        field = etree.Element('field')
        field.set('name', field_name)
        field.set('groups', 'mai_product_pricelist_dynamic_listview.group_product_pricelist')
        field.set('options', "{'digits':[16,2]}")
        xpath.set('expr', expr)
        xpath.append(field)
        return etree.tostring(xpath).decode("utf-8")

    def action_add(self, field_name, label_name):
        self.add_new_dynamic_fields(field_name, label_name)
        arch = '<?xml version="1.0"?>' + str(self.xml_field_arch(field_name, label_name))
        vals = {
            'type': 'tree',
            'model': 'product.product',
            'inherit_id': self.env.ref('product.product_product_tree_view').id,
            'mode': 'extension',
            'arch_base': arch,
            'name': str(self.id),
        }
        ir_model = self.env['ir.model'].search([
            ('model', '=', 'product.product')])
        if hasattr(ir_model, 'module_id'):
            vals.update({'module_id': ir_model.module_id.id})
        self.env['ir.ui.view'].sudo().create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }