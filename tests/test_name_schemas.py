import unittest

from pydantic import ValidationError

from schemas.name_schemas import BirthInfo, NameIn, NameResultSchema


class NameSchemaTests(unittest.TestCase):
    def test_personal_naming_accepts_optional_birth_info(self):
        request = NameIn(
            category="个人/宝宝起名",
            surname="林",
            use_bazi=True,
            birth_info=BirthInfo(birth_date="2026-06-18", birth_time="08:30"),
        )
        self.assertEqual(request.surname, "林")
        self.assertTrue(request.use_bazi)

    def test_bazi_requires_birth_date(self):
        with self.assertRaises(ValidationError):
            NameIn(category="人名", surname="林", use_bazi=True)

    def test_brand_naming_requires_industry_or_requirement(self):
        with self.assertRaises(ValidationError):
            NameIn(category="商业/品牌起名")

    def test_result_report_fields_are_backward_compatible(self):
        result = NameResultSchema.model_validate({
            "names": [{"name": "清和", "reference": "创意组合", "moral": "清朗和美"}]
        })
        self.assertEqual(result.names[0].domain, "")
        self.assertEqual(result.naming_strategy, [])

    def test_baby_type_derives_gender(self):
        request = NameIn(category="宝宝起名", surname="林", person_type="女孩")
        self.assertEqual(request.gender, "女")

    def test_pet_and_virtual_ip_are_separate_categories(self):
        pet = NameIn(category="宠物起名", ip_type="猫")
        virtual_ip = NameIn(category="虚拟IP起名", ip_type="品牌吉祥物")
        self.assertNotEqual(pet.category, virtual_ip.category)


if __name__ == "__main__":
    unittest.main()
